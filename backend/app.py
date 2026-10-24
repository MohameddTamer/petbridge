import base64
import json
import os
import re
import secrets
from datetime import date, datetime, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from breed import analyze_image
from db import audit, check_password, commission_rate, connect, get_setting, hash_password, init_db, now_iso
from taxonomy import SERVICE_INDEX, taxonomy_payload


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
ACTIVE_BOOKING_STATUSES = ("pending", "accepted", "proposed")
STORE_COMMISSION_RATE = 0.10


def public_user(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "role": row["role"],
        "admin_level": row["admin_level"],
        "status": row["status"],
        "warnings": row["warnings"],
        "created_at": row["created_at"],
    }


def provider_dict(conn, row):
    rating_row = conn.execute(
        "SELECT AVG(rating) AS avg_rating, COUNT(*) AS total FROM reviews WHERE provider_id = ?",
        (row["id"],),
    ).fetchone()
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "business_name": row["business_name"],
        "kind": row["kind"],
        "description": row["description"],
        "city": row["city"],
        "area": row["area"],
        "address": row["address"],
        "phone": row["phone"],
        "status": row["status"],
        "plan": row["plan"],
        "featured": bool(row["featured"]),
        "rating": round(rating_row["avg_rating"], 1) if rating_row["avg_rating"] else None,
        "reviews_count": rating_row["total"],
        "created_at": row["created_at"],
    }


def service_dict(row):
    info = SERVICE_INDEX.get(row["taxonomy_key"], {})
    return {
        "id": row["id"],
        "provider_id": row["provider_id"],
        "taxonomy_key": row["taxonomy_key"],
        "name": row["name"],
        "category": row["category"],
        "category_label": info.get("category_label", row["category"]),
        "price": row["price"],
        "duration_min": row["duration_min"],
        "mode": row["mode"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def slot_dict(conn, row):
    booked = conn.execute(
        """
        SELECT COUNT(*) AS c FROM bookings
        WHERE slot_id = ? AND status IN ('pending','accepted','proposed')
        """,
        (row["id"],),
    ).fetchone()["c"]
    return {
        "id": row["id"],
        "provider_id": row["provider_id"],
        "service_id": row["service_id"],
        "date": row["date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "capacity": row["capacity"],
        "booked": booked,
        "remaining": max(row["capacity"] - booked, 0),
        "active": bool(row["active"]),
    }


def age_label(birth_text):
    try:
        born = date.fromisoformat(birth_text)
    except ValueError:
        return ""
    today = date.today()
    months = (today.year - born.year) * 12 + today.month - born.month
    if today.day < born.day:
        months -= 1
    months = max(months, 0)
    years, rest = divmod(months, 12)
    if years and rest:
        return f"{years} {'year' if years == 1 else 'years'} and {rest} {'month' if rest == 1 else 'months'}"
    if years:
        return f"{years} {'year' if years == 1 else 'years'}"
    return f"{rest} {'month' if rest == 1 else 'months'}"


def health_status(next_due):
    if not next_due:
        return "none"
    try:
        due = date.fromisoformat(next_due)
    except ValueError:
        return "none"
    delta = (due - date.today()).days
    if delta < 0:
        return "overdue"
    if delta <= 7:
        return "due_soon"
    return "ok"


def health_dict(row):
    data = dict(row)
    data["status"] = health_status(row["next_due"])
    return data


def pet_dict(conn, row, include_health=True):
    data = {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "name": row["name"],
        "species": row["species"],
        "breed": row["breed"],
        "birth_date": row["birth_date"],
        "age_label": age_label(row["birth_date"]),
        "sex": row["sex"],
        "weight_kg": row["weight_kg"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "health_records": [],
    }
    if include_health:
        records = conn.execute(
            "SELECT * FROM health_records WHERE pet_id = ? ORDER BY COALESCE(next_due, given_date), given_date",
            (row["id"],),
        ).fetchall()
        data["health_records"] = [health_dict(record) for record in records]
    return data


def booking_dict(conn, row):
    return {
        "id": row["id"],
        "customer_id": row["customer_id"],
        "customer_name": row["customer_name"],
        "provider_id": row["provider_id"],
        "business_name": row["business_name"],
        "service_id": row["service_id"],
        "service_name": row["service_name"],
        "pet_id": row["pet_id"],
        "pet_name": row["pet_name"],
        "slot_id": row["slot_id"],
        "start_at": row["start_at"],
        "proposed_start_at": row["proposed_start_at"],
        "status": row["status"],
        "total": row["total"],
        "commission_rate": row["commission_rate"],
        "commission": row["commission"],
        "provider_net": row["provider_net"],
        "payment_status": row["payment_status"],
        "payment_label": "Simulated demo payment" if row["payment_status"] == "simulated_paid" else row["payment_status"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


BOOKING_SELECT = """
SELECT b.*, u.name AS customer_name, p.business_name AS business_name,
       s.name AS service_name, pet.name AS pet_name
FROM bookings b
JOIN users u ON u.id = b.customer_id
JOIN providers p ON p.id = b.provider_id
JOIN services s ON s.id = b.service_id
LEFT JOIN pets pet ON pet.id = b.pet_id
"""


def money_for(total, rate):
    commission = round(float(total) * float(rate), 2)
    return commission, round(float(total) - commission, 2)


def parse_start(slot):
    return f"{slot['date']}T{slot['start_time']}:00"


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Handler(BaseHTTPRequestHandler):
    server_version = "PetBridge/0.1"

    def log_message(self, fmt, *args):
        if os.environ.get("PETBRIDGE_QUIET") != "1":
            super().log_message(fmt, *args)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type):
        if not os.path.isfile(path):
            self.send_json(404, {"error": "File not found"})
            return
        with open(path, "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if path.endswith("sw.js"):
            self.send_header("Service-Worker-Allowed", "/")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "Invalid data format")

    def current_user(self, conn):
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise ApiError(401, "Sign in first")
        token = header[7:].strip()
        row = conn.execute(
            """
            SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise ApiError(401, "Invalid session")
        if row["status"] == "suspended":
            raise ApiError(403, "This account is suspended")
        return row

    def optional_user(self, conn):
        try:
            return self.current_user(conn)
        except ApiError:
            return None

    def provider_for(self, conn, user):
        return conn.execute(
            "SELECT * FROM providers WHERE user_id = ?", (user["id"],)
        ).fetchone()

    def require_provider(self, conn):
        user = self.current_user(conn)
        if user["role"] != "provider":
            raise ApiError(403, "This area is for providers only")
        provider = self.provider_for(conn, user)
        if provider is None:
            raise ApiError(403, "This account has no provider profile")
        return user, provider

    def require_admin(self, conn, levels=None):
        user = self.current_user(conn)
        if user["role"] != "admin":
            raise ApiError(403, "This area is for admin only")
        if levels and user["admin_level"] not in levels:
            raise ApiError(403, "Your admin level does not allow this action")
        return user

    def make_session(self, conn, user_id):
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions(token, user_id, created_at) VALUES(?, ?, ?)",
            (token, user_id, now_iso()),
        )
        return token

    def auth_payload(self, conn, user):
        provider = self.provider_for(conn, user) if user["role"] == "provider" else None
        return {
            "user": public_user(user),
            "provider": provider_dict(conn, provider) if provider else None,
        }

    def do_GET(self):
        self.handle_method("GET")

    def do_POST(self):
        self.handle_method("POST")

    def do_PATCH(self):
        self.handle_method("PATCH")

    def do_DELETE(self):
        self.handle_method("DELETE")

    def handle_method(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        conn = connect()
        try:
            if path.startswith("/api/"):
                payload, status = self.route_api(conn, method, path, query)
                conn.commit()
                self.send_json(status, payload)
            else:
                self.route_static(path)
        except ApiError as err:
            conn.rollback()
            self.send_json(err.status, {"error": err.message})
        except Exception as err:
            conn.rollback()
            self.send_json(500, {"error": f"Internal error: {err}"})
        finally:
            conn.close()

    def route_static(self, path):
        pages = {
            "/": "index.html",
            "/index.html": "index.html",
            "/login": "login.html",
            "/login.html": "login.html",
            "/provider": "provider.html",
            "/provider.html": "provider.html",
            "/admin": "admin.html",
            "/admin.html": "admin.html",
        }
        types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".webmanifest": "application/manifest+json; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
        }
        file_name = pages.get(path, path.lstrip("/"))
        extension = os.path.splitext(file_name)[1]
        if extension not in types or ".." in file_name:
            self.send_json(404, {"error": "Page not found"})
            return
        self.send_file(os.path.join(FRONTEND_DIR, file_name), types[extension])

    def route_api(self, conn, method, path, query):
        if path == "/api/health" and method == "GET":
            return {"ok": True, "service": "PetBridge"}, 200
        if path == "/api/taxonomy" and method == "GET":
            return taxonomy_payload(), 200
        if path == "/api/auth/login" and method == "POST":
            return self.login(conn), 200
        if path == "/api/auth/register-customer" and method == "POST":
            return self.register_customer(conn), 201
        if path == "/api/auth/register-provider" and method == "POST":
            return self.register_provider(conn), 201
        if path == "/api/auth/logout" and method == "POST":
            user = self.current_user(conn)
            token = self.headers.get("Authorization", "")[7:].strip()
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            audit(conn, user, "logout", "user", user["id"])
            return {"ok": True}, 200
        if path == "/api/me" and method == "GET":
            user = self.current_user(conn)
            return self.auth_payload(conn, user), 200
        if path == "/api/directory" and method == "GET":
            return self.directory(conn, query), 200
        if path == "/api/articles" and method == "GET":
            rows = conn.execute("SELECT * FROM articles ORDER BY id").fetchall()
            return {"articles": [dict(row) for row in rows]}, 200
        if path == "/api/products" and method == "GET":
            return self.product_list(conn), 200
        if path.startswith("/api/client/") or path == "/api/pets" or path.startswith("/api/pets/"):
            return self.client_routes(conn, method, path)
        if path == "/api/bookings" and method == "POST":
            return self.create_booking(conn), 201
        match = re.fullmatch(r"/api/bookings/(\d+)/(cancel|respond-proposal)", path)
        if match and method == "POST":
            return self.customer_booking_action(conn, int(match.group(1)), match.group(2)), 200
        if path in ("/api/lost-found", "/api/adoptions", "/api/posts") :
            return self.community_routes(conn, method, path), 200 if method == "GET" else 201
        match = re.fullmatch(r"/api/posts/(\d+)/(comments|report)", path)
        if match and method == "POST":
            return self.post_action(conn, int(match.group(1)), match.group(2)), 201
        if path == "/api/orders" and method == "POST":
            return self.create_order(conn), 201
        if path == "/api/breed/analyze" and method == "POST":
            return self.breed_analyze(conn), 200
        if path.startswith("/api/provider/"):
            return self.provider_routes(conn, method, path), 200
        if path.startswith("/api/admin/"):
            return self.admin_routes(conn, method, path), 200
        raise ApiError(404, "Route not found")

    def login(self, conn):
        data = self.read_json()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password(password, user["password_hash"], user["salt"]):
            raise ApiError(401, "Incorrect sign-in details")
        if user["status"] == "suspended":
            raise ApiError(403, "This account is suspended")
        token = self.make_session(conn, user["id"])
        payload = self.auth_payload(conn, user)
        payload["token"] = token
        audit(conn, user, "login", "user", user["id"])
        return payload

    def register_customer(self, conn):
        data = self.read_json()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not name or "@" not in email or len(password) < 8:
            raise ApiError(400, "Enter a name, a valid email and a password of at least 8 characters")
        if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            raise ApiError(409, "This email is already registered")
        digest, salt = hash_password(password)
        cur = conn.execute(
            """
            INSERT INTO users(name, email, phone, password_hash, salt, role, status, created_at)
            VALUES(?, ?, ?, ?, ?, 'customer', 'active', ?)
            """,
            (name, email, str(data.get("phone", "")), digest, salt, now_iso()),
        )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        token = self.make_session(conn, user["id"])
        payload = self.auth_payload(conn, user)
        payload["token"] = token
        audit(conn, user, "register_customer", "user", user["id"])
        return payload

    def register_provider(self, conn):
        data = self.read_json()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        business = str(data.get("business_name", "")).strip()
        city = str(data.get("city", "")).strip()
        if not name or not business or not city or "@" not in email or len(password) < 8:
            raise ApiError(400, "Provider details are missing or invalid")
        if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            raise ApiError(409, "This email is already registered")
        digest, salt = hash_password(password)
        cur = conn.execute(
            """
            INSERT INTO users(name, email, phone, password_hash, salt, role, status, created_at)
            VALUES(?, ?, ?, ?, ?, 'provider', 'active', ?)
            """,
            (name, email, str(data.get("phone", "")), digest, salt, now_iso()),
        )
        user_id = cur.lastrowid
        provider_cur = conn.execute(
            """
            INSERT INTO providers(user_id, business_name, kind, description, city, area, address, phone, status, plan, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'basic', ?)
            """,
            (
                user_id,
                business,
                str(data.get("kind", "mixed")),
                str(data.get("description", "")),
                city,
                str(data.get("area", "")),
                str(data.get("address", "")),
                str(data.get("phone", "")),
                now_iso(),
            ),
        )
        provider_id = provider_cur.lastrowid
        documents = data.get("documents") or []
        if not documents:
            documents = [{"doc_type": "license", "label": "Business document", "file_name": "not-provided"}]
        for doc in documents[:10]:
            conn.execute(
                """
                INSERT INTO provider_documents(provider_id, doc_type, label, file_name, status, created_at)
                VALUES(?, ?, ?, ?, 'pending', ?)
                """,
                (
                    provider_id,
                    str(doc.get("doc_type", "document"))[:50],
                    str(doc.get("label", "Document"))[:150],
                    str(doc.get("file_name", ""))[:255],
                    now_iso(),
                ),
            )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        token = self.make_session(conn, user["id"])
        payload = self.auth_payload(conn, user)
        payload["token"] = token
        audit(conn, user, "register_provider_pending", "provider", provider_id, business)
        return payload

    def directory(self, conn, query):
        city = (query.get("city") or [""])[0].strip()
        category = (query.get("category") or [""])[0].strip()
        text = (query.get("q") or [""])[0].strip()
        providers = conn.execute(
            """
            SELECT p.* FROM providers p JOIN users u ON u.id = p.user_id
            WHERE p.status = 'approved' AND u.status = 'active'
            ORDER BY p.featured DESC, p.id
            """
        ).fetchall()
        result = []
        for provider in providers:
            services = conn.execute(
                """
                SELECT * FROM services WHERE provider_id = ? AND status = 'approved'
                ORDER BY category, id
                """,
                (provider["id"],),
            ).fetchall()
            visible_services = []
            for service in services:
                if category and service["category"] != category:
                    continue
                if text and text not in service["name"] and text not in provider["business_name"]:
                    continue
                item = service_dict(service)
                slots = conn.execute(
                    """
                    SELECT * FROM availability
                    WHERE provider_id = ? AND (service_id = ? OR service_id IS NULL)
                      AND active = 1 AND date >= date('now','localtime')
                    ORDER BY date, start_time
                    """,
                    (provider["id"], service["id"]),
                ).fetchall()
                item["slots"] = [slot_dict(conn, slot) for slot in slots]
                visible_services.append(item)
            if city and provider["city"] != city:
                continue
            if (category or text) and not visible_services:
                continue
            entry = provider_dict(conn, provider)
            entry["services"] = visible_services
            result.append(entry)
        return {"providers": result}

    def product_list(self, conn):
        rows = conn.execute(
            """
            SELECT pr.*, p.business_name, p.city FROM products pr
            JOIN providers p ON p.id = pr.provider_id
            JOIN users u ON u.id = p.user_id
            WHERE pr.status = 'approved' AND p.status = 'approved' AND u.status = 'active'
            ORDER BY pr.id
            """
        ).fetchall()
        return {"products": [dict(row) for row in rows]}

    def client_routes(self, conn, method, path):
        user = self.current_user(conn)
        if user["role"] != "customer":
            raise ApiError(403, "This area is for customers only")
        if path == "/api/client/home" and method == "GET":
            pets = conn.execute(
                "SELECT * FROM pets WHERE owner_id = ? ORDER BY id", (user["id"],)
            ).fetchall()
            pet_data = [pet_dict(conn, pet) for pet in pets]
            due = []
            for pet in pet_data:
                for record in pet["health_records"]:
                    if record["status"] in ("overdue", "due_soon"):
                        item = dict(record)
                        item["pet_name"] = pet["name"]
                        item["pet_id"] = pet["id"]
                        due.append(item)
            due.sort(key=lambda item: item.get("next_due") or "9999-12-31")
            bookings = self.booking_rows(conn, "b.customer_id = ?", (user["id"],), limit=10)
            return {"pets": pet_data, "due": due, "bookings": bookings, "notifications": []}, 200
        if path == "/api/client/bookings" and method == "GET":
            return {"bookings": self.booking_rows(conn, "b.customer_id = ?", (user["id"],))}, 200
        if path == "/api/pets" and method == "POST":
            data = self.read_json()
            name = str(data.get("name", "")).strip()
            species = str(data.get("species", "")).strip()
            birth = str(data.get("birth_date", "")).strip()
            try:
                date.fromisoformat(birth)
            except ValueError:
                raise ApiError(400, "Invalid birth date")
            if not name or not species:
                raise ApiError(400, "Pet name and species are required")
            cur = conn.execute(
                """
                INSERT INTO pets(owner_id, name, species, breed, birth_date, sex, weight_kg, notes, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    name,
                    species,
                    str(data.get("breed", "")),
                    birth,
                    str(data.get("sex", "")),
                    data.get("weight_kg"),
                    str(data.get("notes", "")),
                    now_iso(),
                ),
            )
            pet = conn.execute("SELECT * FROM pets WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_pet", "pet", pet["id"], name)
            return {"pet": pet_dict(conn, pet)}, 201
        match = re.fullmatch(r"/api/pets/(\d+)/health", path)
        if match and method == "POST":
            pet_id = int(match.group(1))
            pet = conn.execute(
                "SELECT * FROM pets WHERE id = ? AND owner_id = ?", (pet_id, user["id"])
            ).fetchone()
            if pet is None:
                raise ApiError(404, "Pet not found")
            data = self.read_json()
            given = str(data.get("given_date", "")).strip()
            next_due = str(data.get("next_due", "")).strip() or None
            try:
                date.fromisoformat(given)
                if next_due:
                    date.fromisoformat(next_due)
            except ValueError:
                raise ApiError(400, "Invalid health record dates")
            cur = conn.execute(
                """
                INSERT INTO health_records(pet_id, kind, name, given_date, next_due, provider_name, notes, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pet_id,
                    str(data.get("kind", "checkup")),
                    str(data.get("name", "")).strip(),
                    given,
                    next_due,
                    str(data.get("provider_name", "")),
                    str(data.get("notes", "")),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM health_records WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_health_record", "pet", pet_id, row["name"])
            return {"record": health_dict(row)}, 201
        raise ApiError(404, "Route not found")

    def booking_rows(self, conn, where, params, limit=None):
        sql = BOOKING_SELECT + f" WHERE {where} ORDER BY b.created_at DESC, b.id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql, params).fetchall()
        return [booking_dict(conn, row) for row in rows]

    def create_booking(self, conn):
        user = self.current_user(conn)
        if user["role"] != "customer":
            raise ApiError(403, "Booking is for customers only")
        data = self.read_json()
        service_id = data.get("service_id")
        service = conn.execute(
            """
            SELECT s.*, p.status AS provider_status, u.status AS user_status
            FROM services s JOIN providers p ON p.id = s.provider_id JOIN users u ON u.id = p.user_id
            WHERE s.id = ?
            """,
            (service_id,),
        ).fetchone()
        if service is None or service["status"] != "approved" or service["provider_status"] != "approved" or service["user_status"] != "active":
            raise ApiError(404, "This service is not available for booking")
        pet_id = data.get("pet_id")
        if pet_id:
            pet = conn.execute(
                "SELECT id FROM pets WHERE id = ? AND owner_id = ?", (pet_id, user["id"])
            ).fetchone()
            if pet is None:
                raise ApiError(400, "The selected pet does not belong to this account")
        slot = None
        slot_id = data.get("slot_id")
        if slot_id:
            slot = conn.execute(
                """
                SELECT * FROM availability
                WHERE id = ? AND provider_id = ? AND (service_id = ? OR service_id IS NULL) AND active = 1
                """,
                (slot_id, service["provider_id"], service_id),
            ).fetchone()
            if slot is None:
                raise ApiError(400, "The selected slot is not available")
            if slot["date"] < date.today().isoformat():
                raise ApiError(400, "The selected slot has passed")
            booked = conn.execute(
                """
                SELECT COUNT(*) AS c FROM bookings WHERE slot_id = ? AND status IN ('pending','accepted','proposed')
                """,
                (slot_id,),
            ).fetchone()["c"]
            if booked >= slot["capacity"]:
                raise ApiError(409, "This slot is fully booked")
            start_at = parse_start(slot)
        else:
            raw_start = str(data.get("start_at", "")).strip()
            if not raw_start:
                raise ApiError(400, "Pick an available slot or set a start time")
            start_at = raw_start
        rate = commission_rate(conn)
        commission, net = money_for(service["price"], rate)
        cur = conn.execute(
            """
            INSERT INTO bookings(customer_id, provider_id, service_id, pet_id, slot_id, start_at, status, total,
                                 commission_rate, commission, provider_net, payment_status, notes, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, 'simulated_paid', ?, ?, ?)
            """,
            (
                user["id"],
                service["provider_id"],
                service_id,
                pet_id,
                slot_id,
                start_at,
                service["price"],
                rate,
                commission,
                net,
                str(data.get("notes", "")),
                now_iso(),
                now_iso(),
            ),
        )
        booking_id = cur.lastrowid
        audit(conn, user, "create_booking", "booking", booking_id, f"total {service['price']}")
        row = conn.execute(BOOKING_SELECT + " WHERE b.id = ?", (booking_id,)).fetchone()
        return {"booking": booking_dict(conn, row)}

    def customer_booking_action(self, conn, booking_id, action):
        user = self.current_user(conn)
        if user["role"] != "customer":
            raise ApiError(403, "Only the customer who owns this booking can do this")
        booking = conn.execute(
            "SELECT * FROM bookings WHERE id = ? AND customer_id = ?", (booking_id, user["id"])
        ).fetchone()
        if booking is None:
            raise ApiError(404, "Booking not found")
        data = self.read_json() if action == "respond-proposal" else {}
        if action == "cancel":
            if booking["status"] not in ACTIVE_BOOKING_STATUSES:
                raise ApiError(409, "A finished or completed booking cannot be cancelled")
            conn.execute(
                "UPDATE bookings SET status = 'cancelled', updated_at = ? WHERE id = ?",
                (now_iso(), booking_id),
            )
            audit(conn, user, "cancel_booking", "booking", booking_id)
        else:
            if booking["status"] != "proposed" or not booking["proposed_start_at"]:
                raise ApiError(409, "There is no proposed slot waiting for a reply")
            if data.get("accept"):
                conn.execute(
                    """
                    UPDATE bookings SET status = 'accepted', start_at = proposed_start_at,
                    proposed_start_at = NULL, updated_at = ? WHERE id = ?
                    """,
                    (now_iso(), booking_id),
                )
                audit(conn, user, "accept_booking_proposal", "booking", booking_id)
            else:
                conn.execute(
                    "UPDATE bookings SET status = 'cancelled', proposed_start_at = NULL, updated_at = ? WHERE id = ?",
                    (now_iso(), booking_id),
                )
                audit(conn, user, "reject_booking_proposal", "booking", booking_id)
        row = conn.execute(BOOKING_SELECT + " WHERE b.id = ?", (booking_id,)).fetchone()
        return {"booking": booking_dict(conn, row)}

    def community_routes(self, conn, method, path):
        if method == "GET":
            if path == "/api/lost-found":
                rows = conn.execute(
                    """
                    SELECT lf.*, u.name AS author_name FROM lost_found lf JOIN users u ON u.id = lf.author_id
                    ORDER BY lf.id DESC
                    """
                ).fetchall()
                return {"items": [dict(row) for row in rows]}
            if path == "/api/adoptions":
                rows = conn.execute(
                    """
                    SELECT a.*, u.name AS author_name FROM adoptions a JOIN users u ON u.id = a.author_id
                    ORDER BY a.id DESC
                    """
                ).fetchall()
                return {"items": [dict(row) for row in rows]}
            rows = conn.execute(
                """
                SELECT p.*, u.name AS author_name FROM posts p JOIN users u ON u.id = p.author_id
                WHERE p.status = 'visible' ORDER BY p.id DESC
                """
            ).fetchall()
            posts = []
            for row in rows:
                item = dict(row)
                comments = conn.execute(
                    """
                    SELECT c.*, u.name AS author_name FROM comments c JOIN users u ON u.id = c.author_id
                    WHERE c.post_id = ? ORDER BY c.id
                    """,
                    (row["id"],),
                ).fetchall()
                item["comments"] = [dict(comment) for comment in comments]
                posts.append(item)
            return {"posts": posts}
        user = self.current_user(conn)
        data = self.read_json()
        if path == "/api/lost-found":
            kind = data.get("kind")
            if kind not in ("lost", "found"):
                raise ApiError(400, "Invalid report type")
            cur = conn.execute(
                """
                INSERT INTO lost_found(author_id, kind, title, description, pet_name, species, city, area, contact_phone, status, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """,
                (
                    user["id"],
                    kind,
                    str(data.get("title", "")).strip(),
                    str(data.get("description", "")),
                    str(data.get("pet_name", "")),
                    str(data.get("species", "")),
                    str(data.get("city", "")).strip(),
                    str(data.get("area", "")),
                    str(data.get("contact_phone", "")),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM lost_found WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_lost_found", "lost_found", row["id"], row["title"])
            return {"item": dict(row)}
        if path == "/api/adoptions":
            cur = conn.execute(
                """
                INSERT INTO adoptions(author_id, title, animal_name, species, breed, age_label, city, description, contact_phone, status, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', ?)
                """,
                (
                    user["id"],
                    str(data.get("title", "")).strip(),
                    str(data.get("animal_name", "")).strip(),
                    str(data.get("species", "")).strip(),
                    str(data.get("breed", "")),
                    str(data.get("age_label", "")),
                    str(data.get("city", "")).strip(),
                    str(data.get("description", "")),
                    str(data.get("contact_phone", "")),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM adoptions WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_adoption", "adoption", row["id"], row["title"])
            return {"item": dict(row)}
        title = str(data.get("title", "")).strip()
        body = str(data.get("body", "")).strip()
        if not title or not body:
            raise ApiError(400, "Post title and body are required")
        cur = conn.execute(
            "INSERT INTO posts(author_id, title, body, status, created_at) VALUES(?, ?, ?, 'visible', ?)",
            (user["id"], title, body, now_iso()),
        )
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (cur.lastrowid,)).fetchone()
        audit(conn, user, "create_post", "post", row["id"], title)
        return {"post": dict(row)}

    def post_action(self, conn, post_id, action):
        user = self.current_user(conn)
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None or post["status"] != "visible":
            raise ApiError(404, "Post not found")
        data = self.read_json()
        if action == "comments":
            body = str(data.get("body", "")).strip()
            if not body:
                raise ApiError(400, "Comment text is required")
            cur = conn.execute(
                "INSERT INTO comments(post_id, author_id, body, created_at) VALUES(?, ?, ?, ?)",
                (post_id, user["id"], body, now_iso()),
            )
            row = conn.execute("SELECT * FROM comments WHERE id = ?", (cur.lastrowid,)).fetchone()
            return {"comment": dict(row)}
        reason = str(data.get("reason", "")).strip() or "Report from a user"
        cur = conn.execute(
            "INSERT INTO reports(reporter_id, post_id, reason, status, created_at) VALUES(?, ?, ?, 'open', ?)",
            (user["id"], post_id, reason, now_iso()),
        )
        audit(conn, user, "report_post", "post", post_id, reason)
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (cur.lastrowid,)).fetchone()
        return {"report": dict(row)}

    def create_order(self, conn):
        user = self.current_user(conn)
        if user["role"] != "customer":
            raise ApiError(403, "Ordering products is for customers only")
        data = self.read_json()
        qty = int(data.get("qty") or 1)
        product = conn.execute(
            """
            SELECT pr.*, p.status AS provider_status FROM products pr JOIN providers p ON p.id = pr.provider_id
            WHERE pr.id = ? AND pr.status = 'approved'
            """,
            (data.get("product_id"),),
        ).fetchone()
        if product is None or product["provider_status"] != "approved":
            raise ApiError(404, "Product not available")
        if qty < 1 or qty > product["stock"]:
            raise ApiError(400, "Quantity not available")
        total = round(product["price"] * qty, 2)
        commission, net = money_for(total, STORE_COMMISSION_RATE)
        cur = conn.execute(
            """
            INSERT INTO orders(customer_id, provider_id, product_id, qty, total, commission_rate, commission, provider_net,
                               payment_status, status, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'simulated_paid', 'placed', ?)
            """,
            (user["id"], product["provider_id"], product["id"], qty, total, STORE_COMMISSION_RATE, commission, net, now_iso()),
        )
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product["id"]))
        audit(conn, user, "create_simulated_order", "order", cur.lastrowid, f"total {total}")
        return {
            "order": {"id": cur.lastrowid, "total": total, "commission": commission, "provider_net": net},
            "payment_label": "Simulated demo payment, not a real payment gateway",
        }

    def breed_analyze(self, conn):
        user = self.current_user(conn)
        data = self.read_json()
        image_bytes = b""
        encoded = data.get("image_base64")
        if encoded:
            try:
                image_bytes = base64.b64decode(str(encoded).split(",")[-1], validate=False)[:2_000_000]
            except Exception:
                image_bytes = b""
        if not image_bytes:
            image_bytes = str(data.get("file_name", "")).encode("utf-8")
        result = analyze_image(
            str(data.get("file_name", "pet-photo.jpg")),
            str(data.get("declared_species", "other")),
            image_bytes,
        )
        cur = conn.execute(
            """
            INSERT INTO breed_analyses(user_id, pet_id, file_name, declared_species, result_json, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                data.get("pet_id"),
                str(data.get("file_name", "pet-photo.jpg")),
                str(data.get("declared_species", "other")),
                json.dumps(result, ensure_ascii=False),
                now_iso(),
            ),
        )
        result["id"] = cur.lastrowid
        audit(conn, user, "breed_analysis_beta", "breed_analysis", cur.lastrowid, result["breed"])
        return result

    def provider_routes(self, conn, method, path):
        user, provider = self.require_provider(conn)
        if path == "/api/provider/dashboard" and method == "GET":
            services = conn.execute(
                "SELECT * FROM services WHERE provider_id = ? ORDER BY id DESC", (provider["id"],)
            ).fetchall()
            slots = conn.execute(
                "SELECT * FROM availability WHERE provider_id = ? ORDER BY date, start_time", (provider["id"],)
            ).fetchall()
            documents = conn.execute(
                "SELECT * FROM provider_documents WHERE provider_id = ? ORDER BY id", (provider["id"],)
            ).fetchall()
            reviews = conn.execute(
                """
                SELECT r.*, u.name AS customer_name FROM reviews r JOIN users u ON u.id = r.customer_id
                WHERE r.provider_id = ? ORDER BY r.id DESC
                """,
                (provider["id"],),
            ).fetchall()
            products = conn.execute(
                "SELECT * FROM products WHERE provider_id = ? ORDER BY id DESC", (provider["id"],)
            ).fetchall()
            orders = conn.execute(
                "SELECT * FROM orders WHERE provider_id = ? ORDER BY id DESC", (provider["id"],)
            ).fetchall()
            bookings = self.booking_rows(conn, "b.provider_id = ?", (provider["id"],))
            completed = [item for item in bookings if item["status"] == "completed"]
            earnings = {
                "gross": round(sum(item["total"] for item in completed), 2),
                "commission": round(sum(item["commission"] for item in completed), 2),
                "net": round(sum(item["provider_net"] for item in completed), 2),
                "completed_count": len(completed),
                "commission_rate": commission_rate(conn),
            }
            stats = {
                "pending_bookings": len([b for b in bookings if b["status"] == "pending"]),
                "accepted_bookings": len([b for b in bookings if b["status"] == "accepted"]),
                "completed_bookings": len(completed),
                "gross": earnings["gross"],
                "commission": earnings["commission"],
                "net": earnings["net"],
                "rating": provider_dict(conn, provider)["rating"],
            }
            return {
                "provider": provider_dict(conn, provider),
                "stats": stats,
                "bookings": bookings,
                "services": [service_dict(row) for row in services],
                "availability": [slot_dict(conn, row) for row in slots],
                "documents": [dict(row) for row in documents],
                "reviews": [dict(row) for row in reviews],
                "products": [dict(row) for row in products],
                "orders": [dict(row) for row in orders],
                "earnings": earnings,
                "taxonomy": taxonomy_payload(),
            }
        if path == "/api/provider/profile" and method == "PATCH":
            data = self.read_json()
            allowed = ("business_name", "kind", "description", "city", "area", "address", "phone", "plan")
            changes = {key: str(data[key]) for key in allowed if key in data}
            if changes:
                sql = ", ".join(f"{key} = ?" for key in changes)
                conn.execute(f"UPDATE providers SET {sql} WHERE id = ?", (*changes.values(), provider["id"]))
                audit(conn, user, "update_provider_profile", "provider", provider["id"], ", ".join(changes.keys()))
            row = conn.execute("SELECT * FROM providers WHERE id = ?", (provider["id"],)).fetchone()
            return {"provider": provider_dict(conn, row)}
        if path == "/api/provider/services" and method == "POST":
            data = self.read_json()
            taxonomy_key = str(data.get("taxonomy_key", ""))
            if taxonomy_key not in SERVICE_INDEX:
                raise ApiError(400, "Choose a service from the approved taxonomy")
            info = SERVICE_INDEX[taxonomy_key]
            name = str(data.get("name", "")).strip() or info["label"]
            price = float(data.get("price") or 0)
            cur = conn.execute(
                """
                INSERT INTO services(provider_id, taxonomy_key, name, category, price, duration_min, mode, status, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    provider["id"],
                    taxonomy_key,
                    name,
                    info["category"],
                    price,
                    int(data.get("duration_min") or 60),
                    str(data.get("mode", "onsite")),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM services WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_service_pending", "service", row["id"], name)
            return {"service": service_dict(row)}
        match = re.fullmatch(r"/api/provider/services/(\d+)", path)
        if match and method in ("PATCH", "DELETE"):
            service_id = int(match.group(1))
            service = conn.execute(
                "SELECT * FROM services WHERE id = ? AND provider_id = ?", (service_id, provider["id"])
            ).fetchone()
            if service is None:
                raise ApiError(404, "Service not found")
            if method == "DELETE":
                conn.execute("UPDATE services SET status = 'hidden' WHERE id = ?", (service_id,))
                audit(conn, user, "hide_service", "service", service_id)
                return {"ok": True}
            data = self.read_json()
            price = float(data.get("price", service["price"]))
            name = str(data.get("name", service["name"]))
            duration = int(data.get("duration_min", service["duration_min"]))
            mode = str(data.get("mode", service["mode"]))
            conn.execute(
                """
                UPDATE services SET name = ?, price = ?, duration_min = ?, mode = ?, status = 'pending'
                WHERE id = ?
                """,
                (name, price, duration, mode, service_id),
            )
            audit(conn, user, "edit_service_pending", "service", service_id)
            row = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
            return {"service": service_dict(row)}
        if path == "/api/provider/availability" and method == "POST":
            if provider["status"] != "approved":
                raise ApiError(403, "Slots cannot be opened before the business is approved")
            data = self.read_json()
            day = str(data.get("date", ""))
            try:
                date.fromisoformat(day)
                time.fromisoformat(str(data.get("start_time", "")))
                time.fromisoformat(str(data.get("end_time", "")))
            except ValueError:
                raise ApiError(400, "Invalid slot data")
            service_id = data.get("service_id")
            if service_id:
                owned = conn.execute(
                    "SELECT id FROM services WHERE id = ? AND provider_id = ? AND status = 'approved'",
                    (service_id, provider["id"]),
                ).fetchone()
                if owned is None:
                    raise ApiError(400, "The service is not approved or does not belong to this business")
            cur = conn.execute(
                """
                INSERT INTO availability(provider_id, service_id, date, start_time, end_time, capacity, active, created_at)
                VALUES(?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    provider["id"],
                    service_id,
                    day,
                    str(data.get("start_time")),
                    str(data.get("end_time")),
                    int(data.get("capacity") or 1),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM availability WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_availability", "availability", row["id"], day)
            return {"slot": slot_dict(conn, row)}
        match = re.fullmatch(r"/api/provider/bookings/(\d+)/action", path)
        if match and method == "POST":
            return self.provider_booking_action(conn, user, provider, int(match.group(1)))
        if path == "/api/provider/documents" and method == "POST":
            data = self.read_json()
            cur = conn.execute(
                """
                INSERT INTO provider_documents(provider_id, doc_type, label, file_name, status, created_at)
                VALUES(?, ?, ?, ?, 'pending', ?)
                """,
                (
                    provider["id"],
                    str(data.get("doc_type", "document")),
                    str(data.get("label", "Document")),
                    str(data.get("file_name", "")),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM provider_documents WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "add_provider_document", "provider", provider["id"], row["label"])
            return {"document": dict(row)}
        if path == "/api/provider/products" and method == "POST":
            data = self.read_json()
            cur = conn.execute(
                """
                INSERT INTO products(provider_id, name, description, price, stock, status, created_at)
                VALUES(?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    provider["id"],
                    str(data.get("name", "")).strip(),
                    str(data.get("description", "")),
                    float(data.get("price") or 0),
                    int(data.get("stock") or 0),
                    now_iso(),
                ),
            )
            row = conn.execute("SELECT * FROM products WHERE id = ?", (cur.lastrowid,)).fetchone()
            audit(conn, user, "create_product_pending", "product", row["id"], row["name"])
            return {"product": dict(row)}
        raise ApiError(404, "Route not found")

    def provider_booking_action(self, conn, user, provider, booking_id):
        booking = conn.execute(
            "SELECT * FROM bookings WHERE id = ? AND provider_id = ?", (booking_id, provider["id"])
        ).fetchone()
        if booking is None:
            raise ApiError(404, "Booking not found")
        data = self.read_json()
        action = data.get("action")
        if action == "accept":
            if booking["status"] not in ("pending", "proposed"):
                raise ApiError(409, "This booking is not waiting for acceptance")
            conn.execute("UPDATE bookings SET status = 'accepted', updated_at = ? WHERE id = ?", (now_iso(), booking_id))
        elif action == "reject":
            if booking["status"] not in ACTIVE_BOOKING_STATUSES:
                raise ApiError(409, "A finished booking cannot be rejected")
            conn.execute("UPDATE bookings SET status = 'rejected', updated_at = ? WHERE id = ?", (now_iso(), booking_id))
        elif action == "propose":
            if booking["status"] != "pending":
                raise ApiError(409, "Proposing a slot is only available for pending bookings")
            proposed = str(data.get("proposed_start_at", "")).strip()
            if not proposed:
                raise ApiError(400, "Enter the proposed slot")
            conn.execute(
                "UPDATE bookings SET status = 'proposed', proposed_start_at = ?, updated_at = ? WHERE id = ?",
                (proposed, now_iso(), booking_id),
            )
        elif action == "complete":
            if booking["status"] != "accepted":
                raise ApiError(409, "A booking can only be completed after acceptance")
            conn.execute("UPDATE bookings SET status = 'completed', updated_at = ? WHERE id = ?", (now_iso(), booking_id))
        else:
            raise ApiError(400, "Unknown booking action")
        audit(conn, user, f"booking_{action}", "booking", booking_id)
        row = conn.execute(BOOKING_SELECT + " WHERE b.id = ?", (booking_id,)).fetchone()
        return {"booking": booking_dict(conn, row)}

    def admin_routes(self, conn, method, path):
        if path == "/api/admin/dashboard" and method == "GET":
            self.require_admin(conn)
            return self.admin_dashboard(conn)
        if path == "/api/admin/settings" and method == "GET":
            self.require_admin(conn)
            return {
                "commission_rate": commission_rate(conn),
                "store_commission_rate": STORE_COMMISSION_RATE,
            }
        if path == "/api/admin/settings" and method == "POST":
            admin = self.require_admin(conn, ("super_admin",))
            data = self.read_json()
            rate = float(data.get("commission_rate"))
            if rate < 0 or rate > 0.5:
                raise ApiError(400, "Commission rate is outside the allowed range")
            conn.execute(
                "INSERT INTO settings(key, value) VALUES('commission_rate', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(rate),),
            )
            audit(conn, admin, "update_commission_rate", "setting", None, str(rate))
            return {"commission_rate": rate, "store_commission_rate": STORE_COMMISSION_RATE}
        if path == "/api/admin/approve" and method == "POST":
            admin = self.require_admin(conn, ("super_admin", "moderator"))
            return self.admin_approve(conn, admin)
        match = re.fullmatch(r"/api/admin/users/(\d+)/status", path)
        if match and method == "POST":
            admin = self.require_admin(conn, ("super_admin",))
            data = self.read_json()
            status = data.get("status")
            if status not in ("active", "suspended"):
                raise ApiError(400, "Invalid account status")
            user_id = int(match.group(1))
            target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if target is None:
                raise ApiError(404, "User not found")
            conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
            audit(conn, admin, f"user_{status}", "user", user_id, target["email"])
            return {"user": public_user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())}
        match = re.fullmatch(r"/api/admin/posts/(\d+)/moderate", path)
        if match and method == "POST":
            admin = self.require_admin(conn, ("super_admin", "moderator"))
            data = self.read_json()
            action = data.get("action")
            post_id = int(match.group(1))
            post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
            if post is None:
                raise ApiError(404, "Post not found")
            if action == "hide":
                conn.execute("UPDATE posts SET status = 'hidden' WHERE id = ?", (post_id,))
                conn.execute("UPDATE reports SET status = 'resolved' WHERE post_id = ? AND status = 'open'", (post_id,))
            elif action == "warn":
                conn.execute("UPDATE users SET warnings = warnings + 1 WHERE id = ?", (post["author_id"],))
                conn.execute("UPDATE reports SET status = 'resolved' WHERE post_id = ? AND status = 'open'", (post_id,))
            else:
                raise ApiError(400, "Unknown moderation action")
            audit(conn, admin, f"post_{action}", "post", post_id, post["title"])
            return {"ok": True, "action": action}
        raise ApiError(404, "Route not found")

    def admin_dashboard(self, conn):
        counts = {}
        counts["users"] = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        counts["customers"] = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'customer'").fetchone()["c"]
        counts["providers"] = conn.execute("SELECT COUNT(*) AS c FROM providers").fetchone()["c"]
        counts["pending_providers"] = conn.execute("SELECT COUNT(*) AS c FROM providers WHERE status = 'pending'").fetchone()["c"]
        counts["bookings"] = conn.execute("SELECT COUNT(*) AS c FROM bookings").fetchone()["c"]
        counts["completed_bookings"] = conn.execute("SELECT COUNT(*) AS c FROM bookings WHERE status = 'completed'").fetchone()["c"]
        counts["orders"] = conn.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        counts["open_reports"] = conn.execute("SELECT COUNT(*) AS c FROM reports WHERE status = 'open'").fetchone()["c"]
        money = conn.execute(
            """
            SELECT COALESCE(SUM(total),0) AS gross, COALESCE(SUM(commission),0) AS commission
            FROM bookings WHERE status = 'completed'
            """
        ).fetchone()
        order_money = conn.execute("SELECT COALESCE(SUM(commission),0) AS commission FROM orders").fetchone()
        counts["gross_total"] = round(money["gross"], 2)
        counts["commission_total"] = round(money["commission"] + order_money["commission"], 2)
        counts["booking_commission_total"] = round(money["commission"], 2)
        counts["order_commission_total"] = round(order_money["commission"], 2)

        pending_providers = conn.execute(
            """
            SELECT p.*, u.name AS owner_name, u.email AS owner_email FROM providers p JOIN users u ON u.id = p.user_id
            WHERE p.status = 'pending' ORDER BY p.id
            """
        ).fetchall()
        provider_queue = []
        for row in pending_providers:
            item = provider_dict(conn, row)
            item["owner_name"] = row["owner_name"]
            item["owner_email"] = row["owner_email"]
            docs = conn.execute(
                "SELECT * FROM provider_documents WHERE provider_id = ?", (row["id"],)
            ).fetchall()
            item["documents"] = [dict(doc) for doc in docs]
            provider_queue.append(item)
        pending_services = conn.execute(
            """
            SELECT s.*, p.business_name FROM services s JOIN providers p ON p.id = s.provider_id
            WHERE s.status = 'pending' ORDER BY s.id
            """
        ).fetchall()
        pending_products = conn.execute(
            """
            SELECT pr.*, p.business_name FROM products pr JOIN providers p ON p.id = pr.provider_id
            WHERE pr.status = 'pending' ORDER BY pr.id
            """
        ).fetchall()
        users = conn.execute("SELECT * FROM users ORDER BY role, id").fetchall()
        posts = conn.execute(
            """
            SELECT p.*, u.name AS author_name FROM posts p JOIN users u ON u.id = p.author_id ORDER BY p.id DESC
            """
        ).fetchall()
        reports = conn.execute(
            """
            SELECT r.*, u.name AS reporter_name, p.title AS post_title FROM reports r
            JOIN users u ON u.id = r.reporter_id LEFT JOIN posts p ON p.id = r.post_id ORDER BY r.id DESC
            """
        ).fetchall()
        audit_rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100").fetchall()
        bookings = self.booking_rows(conn, "1 = 1", (), limit=100)
        return {
            "kpis": counts,
            "queues": {
                "providers": provider_queue,
                "services": [dict(row) for row in pending_services],
                "products": [dict(row) for row in pending_products],
            },
            "users": [public_user(row) for row in users],
            "posts": [dict(row) for row in posts],
            "bookings": bookings,
            "audit": [dict(row) for row in audit_rows],
            "reports": [dict(row) for row in reports],
            "settings": {"commission_rate": commission_rate(conn), "store_commission_rate": STORE_COMMISSION_RATE},
        }

    def admin_approve(self, conn, admin):
        data = self.read_json()
        entity = data.get("entity")
        entity_id = data.get("id")
        decision = data.get("decision")
        if decision not in ("approved", "rejected"):
            raise ApiError(400, "Invalid approval decision")
        reason = str(data.get("reason", ""))
        if entity == "provider":
            row = conn.execute("SELECT * FROM providers WHERE id = ?", (entity_id,)).fetchone()
            if row is None:
                raise ApiError(404, "Provider not found")
            conn.execute("UPDATE providers SET status = ? WHERE id = ?", (decision, entity_id))
            if decision == "approved":
                conn.execute("UPDATE provider_documents SET status = 'approved' WHERE provider_id = ?", (entity_id,))
            audit(conn, admin, f"provider_{decision}", "provider", entity_id, reason or row["business_name"])
            return {"provider": provider_dict(conn, conn.execute("SELECT * FROM providers WHERE id = ?", (entity_id,)).fetchone())}
        if entity == "service":
            row = conn.execute("SELECT * FROM services WHERE id = ?", (entity_id,)).fetchone()
            if row is None:
                raise ApiError(404, "Service not found")
            conn.execute("UPDATE services SET status = ? WHERE id = ?", (decision, entity_id))
            audit(conn, admin, f"service_{decision}", "service", entity_id, reason or row["name"])
            return {"service": service_dict(conn.execute("SELECT * FROM services WHERE id = ?", (entity_id,)).fetchone())}
        if entity == "product":
            row = conn.execute("SELECT * FROM products WHERE id = ?", (entity_id,)).fetchone()
            if row is None:
                raise ApiError(404, "Product not found")
            conn.execute("UPDATE products SET status = ? WHERE id = ?", (decision, entity_id))
            audit(conn, admin, f"product_{decision}", "product", entity_id, reason or row["name"])
            return {"product": dict(conn.execute("SELECT * FROM products WHERE id = ?", (entity_id,)).fetchone())}
        raise ApiError(400, "Unknown item type")


def run():
    init_db()
    port = int(os.environ.get("PETBRIDGE_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"PetBridge running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
