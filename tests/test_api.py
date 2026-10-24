import json
import os
import sqlite3
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORT = 8899
BASE = f"http://127.0.0.1:{PORT}"
DB_PATH = Path("/tmp/petbridge-test-api.db")


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(method, path, payload=None, token=None):
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with OPENER.open(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw)
        except ValueError:
            return err.code, {"raw": raw}


def call_raw(path):
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with OPENER.open(req, timeout=5) as response:
            return response.status, response.headers.get_content_type(), response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.headers.get_content_type(), err.read().decode("utf-8")


def login(email, password):
    status, data = call("POST", "/api/auth/login", {"email": email, "password": password})
    assert status == 200, data
    return data["token"]


class PetBridgeApiTest(unittest.TestCase):
    server = None

    @classmethod
    def setUpClass(cls):
        if DB_PATH.exists():
            DB_PATH.unlink()
        env = os.environ.copy()
        env["PETBRIDGE_DB"] = str(DB_PATH)
        env["PETBRIDGE_PORT"] = str(PORT)
        env["PETBRIDGE_QUIET"] = "1"
        cls.server = subprocess.Popen(
            [sys.executable, str(ROOT / "backend" / "app.py")],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(300):
            try:
                status, _ = call("GET", "/api/health")
                if status == 200:
                    break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("server did not start")
        cls.admin = login("admin@petbridge.local", "Admin123!")
        cls.sara = login("sara@petbridge.local", "Sara123!")
        cls.clinic = login("clinic@petbridge.local", "Vet123!")
        cls.pending = login("pending@petbridge.local", "Wait123!")

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server.kill()

    def sql(self, query, params=()):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def test_01_taxonomy_has_35_services(self):
        status, data = call("GET", "/api/taxonomy")
        self.assertEqual(status, 200)
        self.assertEqual(data["service_count"], 35)
        self.assertGreaterEqual(len(data["categories"]), 8)

    def test_02_auth_failures_and_injection(self):
        status, _ = call("POST", "/api/auth/login", {"email": "sara@petbridge.local", "password": "wrong"})
        self.assertEqual(status, 401)
        status, _ = call("GET", "/api/me")
        self.assertEqual(status, 401)
        before = self.sql("SELECT COUNT(*) AS c FROM users")[0]["c"]
        status, _ = call(
            "POST",
            "/api/auth/login",
            {"email": "admin@petbridge.local' OR '1'='1", "password": "anything"},
        )
        self.assertEqual(status, 401)
        after = self.sql("SELECT COUNT(*) AS c FROM users")[0]["c"]
        self.assertEqual(before, after)

    def test_03_passwords_are_pbkdf2_hashes(self):
        row = self.sql("SELECT password_hash, salt FROM users WHERE email = ?", ("sara@petbridge.local",))[0]
        self.assertEqual(len(row["password_hash"]), 64)
        self.assertEqual(len(row["salt"]), 32)
        self.assertNotIn("Sara123", row["password_hash"])

    def test_04_directory_seed_shape(self):
        status, data = call("GET", "/api/directory")
        self.assertEqual(status, 200)
        providers = data["providers"]
        self.assertGreaterEqual(len(providers), 8)
        self.assertGreaterEqual(len({item["city"] for item in providers}), 3)
        categories = {
            service["category"] for item in providers for service in item["services"]
        }
        self.assertGreaterEqual(len(categories), 6)
        self.assertTrue(all(item["status"] == "approved" for item in providers))

    def test_05_home_overdue_and_age(self):
        status, data = call("GET", "/api/client/home", token=self.sara)
        self.assertEqual(status, 200)
        overdue = [item for item in data["due"] if item["status"] == "overdue"]
        self.assertTrue(any(item["name"] == "Rabies vaccination" for item in overdue))
        rocky = next(item for item in data["pets"] if item["name"] == "Rocky")
        self.assertTrue(rocky["age_label"])
        record = next(item for item in rocky["health_records"] if item["name"] == "Rabies vaccination")
        self.assertEqual(record["status"], "overdue")

    def test_06_approval_gate_for_provider_and_service(self):
        email = "gate@petbridge.local"
        status, data = call(
            "POST",
            "/api/auth/register-provider",
            {
                "name": "Gate Approval",
                "email": email,
                "phone": "01099998888",
                "password": "Gate123!",
                "business_name": "Hidden Gate Clinic",
                "kind": "vet",
                "city": "Tanta",
                "area": "El Galaa",
                "address": "Test address",
                "description": "A test clinic for the approval flow",
                "documents": [{"doc_type": "license", "label": "Licence", "file_name": "license.pdf"}],
            },
        )
        self.assertEqual(status, 201)
        token = data["token"]
        provider_id = data["provider"]["id"]
        status, service_data = call(
            "POST",
            "/api/provider/services",
            {"taxonomy_key": "vet_general", "price": 300, "duration_min": 30, "mode": "onsite"},
            token=token,
        )
        self.assertEqual(status, 200)
        service_id = service_data["service"]["id"]
        status, directory = call("GET", "/api/directory?q=" + urllib.parse.quote("Gate"))
        self.assertEqual(status, 200)
        self.assertEqual(directory["providers"], [])
        status, dashboard = call("GET", "/api/admin/dashboard", token=self.admin)
        self.assertEqual(status, 200)
        self.assertIn(provider_id, [item["id"] for item in dashboard["queues"]["providers"]])
        self.assertIn(service_id, [item["id"] for item in dashboard["queues"]["services"]])
        status, _ = call(
            "POST",
            "/api/admin/approve",
            {"entity": "provider", "id": provider_id, "decision": "approved"},
            token=self.admin,
        )
        self.assertEqual(status, 200)
        status, directory = call("GET", "/api/directory?q=" + urllib.parse.quote("Gate"))
        self.assertEqual(directory["providers"], [])
        status, _ = call(
            "POST",
            "/api/admin/approve",
            {"entity": "service", "id": service_id, "decision": "approved"},
            token=self.admin,
        )
        self.assertEqual(status, 200)
        status, directory = call("GET", "/api/directory?q=" + urllib.parse.quote("Gate"))
        self.assertEqual(len(directory["providers"]), 1)
        self.assertEqual(directory["providers"][0]["services"][0]["id"], service_id)
        audit_rows = self.sql(
            "SELECT action FROM audit_log WHERE entity_type IN ('provider','service') AND entity_id IN (?, ?) ORDER BY id",
            (provider_id, service_id),
        )
        actions = [row["action"] for row in audit_rows]
        self.assertIn("provider_approved", actions)
        self.assertIn("service_approved", actions)

    def test_07_role_isolation(self):
        status, _ = call("GET", "/api/admin/dashboard", token=self.clinic)
        self.assertEqual(status, 403)
        status, _ = call("GET", "/api/provider/dashboard", token=self.sara)
        self.assertEqual(status, 403)
        status, _ = call("GET", "/api/client/home", token=self.admin)
        self.assertEqual(status, 403)
        status, _ = call(
            "POST",
            "/api/provider/bookings/1/action",
            {"action": "accept"},
            token=self.sara,
        )
        self.assertEqual(status, 403)

    def test_08_pending_provider_cannot_open_slots(self):
        status, _ = call(
            "POST",
            "/api/provider/availability",
            {"date": "2030-01-01", "start_time": "10:00", "end_time": "10:30", "capacity": 1},
            token=self.pending,
        )
        self.assertEqual(status, 403)

    def test_09_booking_flow_money_and_sql(self):
        _, directory = call("GET", "/api/directory")
        clinic = next(item for item in directory["providers"] if item["business_name"] == "Nile Veterinary Clinic")
        service = next(item for item in clinic["services"] if item["taxonomy_key"] == "vet_vaccine")
        slot = next(item for item in service["slots"] if item["remaining"] > 0)
        _, home = call("GET", "/api/client/home", token=self.sara)
        rocky = next(item for item in home["pets"] if item["name"] == "Rocky")
        status, created = call(
            "POST",
            "/api/bookings",
            {"service_id": service["id"], "pet_id": rocky["id"], "slot_id": slot["id"], "notes": "Test"},
            token=self.sara,
        )
        self.assertEqual(status, 201, created)
        booking = created["booking"]
        self.assertEqual(booking["total"], 350)
        self.assertEqual(booking["commission"], 42)
        self.assertEqual(booking["provider_net"], 308)
        status, accepted = call(
            "POST",
            f"/api/provider/bookings/{booking['id']}/action",
            {"action": "accept"},
            token=self.clinic,
        )
        self.assertEqual(status, 200)
        self.assertEqual(accepted["booking"]["status"], "accepted")
        status, completed = call(
            "POST",
            f"/api/provider/bookings/{booking['id']}/action",
            {"action": "complete"},
            token=self.clinic,
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed["booking"]["status"], "completed")
        row = self.sql(
            "SELECT total, commission, provider_net, status FROM bookings WHERE id = ?", (booking["id"],)
        )[0]
        self.assertEqual((row["total"], row["commission"], row["provider_net"], row["status"]), (350, 42, 308, "completed"))
        _, provider_data = call("GET", "/api/provider/dashboard", token=self.clinic)
        self.assertEqual(provider_data["earnings"]["gross"], 850)
        self.assertEqual(provider_data["earnings"]["commission"], 102)
        self.assertEqual(provider_data["earnings"]["net"], 748)
        _, admin_data = call("GET", "/api/admin/dashboard", token=self.admin)
        admin_booking = next(item for item in admin_data["bookings"] if item["id"] == booking["id"])
        self.assertEqual(admin_booking["commission"], 42)

    def test_10_proposal_flow(self):
        _, directory = call("GET", "/api/directory")
        clinic = next(item for item in directory["providers"] if item["business_name"] == "Nile Veterinary Clinic")
        service = next(item for item in clinic["services"] if item["taxonomy_key"] == "vet_general")
        slot = next(item for item in service["slots"] if item["remaining"] > 0)
        _, home = call("GET", "/api/client/home", token=self.sara)
        pet = home["pets"][0]
        status, created = call(
            "POST",
            "/api/bookings",
            {"service_id": service["id"], "pet_id": pet["id"], "slot_id": slot["id"]},
            token=self.sara,
        )
        self.assertEqual(status, 201, created)
        booking_id = created["booking"]["id"]
        proposed = "2030-02-02T13:00:00"
        status, proposed_data = call(
            "POST",
            f"/api/provider/bookings/{booking_id}/action",
            {"action": "propose", "proposed_start_at": proposed},
            token=self.clinic,
        )
        self.assertEqual(status, 200)
        self.assertEqual(proposed_data["booking"]["status"], "proposed")
        status, answered = call(
            "POST",
            f"/api/bookings/{booking_id}/respond-proposal",
            {"accept": True},
            token=self.sara,
        )
        self.assertEqual(status, 200)
        self.assertEqual(answered["booking"]["status"], "accepted")
        self.assertEqual(answered["booking"]["start_at"], proposed)

    def test_11_product_gate_and_simulated_order(self):
        status, created = call(
            "POST",
            "/api/provider/products",
            {"name": "Gate Approval Product", "description": "Test product", "price": 100, "stock": 5},
            token=self.clinic,
        )
        self.assertEqual(status, 200)
        product_id = created["product"]["id"]
        _, products = call("GET", "/api/products")
        self.assertNotIn(product_id, [item["id"] for item in products["products"]])
        status, _ = call(
            "POST",
            "/api/admin/approve",
            {"entity": "product", "id": product_id, "decision": "approved"},
            token=self.admin,
        )
        self.assertEqual(status, 200)
        _, products = call("GET", "/api/products")
        self.assertIn(product_id, [item["id"] for item in products["products"]])
        status, order = call("POST", "/api/orders", {"product_id": product_id, "qty": 2}, token=self.sara)
        self.assertEqual(status, 201)
        self.assertEqual(order["order"]["total"], 200)
        self.assertEqual(order["order"]["commission"], 20)
        self.assertIn("Simulated", order["payment_label"])
        row = self.sql("SELECT stock FROM products WHERE id = ?", (product_id,))[0]
        self.assertEqual(row["stock"], 3)

    def test_12_breed_beta_is_honest(self):
        status, data = call(
            "POST",
            "/api/breed/analyze",
            {"file_name": "roki-baladi.jpg", "declared_species": "dog"},
            token=self.sara,
        )
        self.assertEqual(status, 200)
        self.assertTrue(data["beta"])
        self.assertEqual(data["breed"], "Baladi")
        self.assertIn("demo", data["note"])
        self.assertNotIn("confidence", data)
        self.assertNotIn("accuracy", data)

    def test_13_community_create_comment_report_and_moderation(self):
        status, created = call(
            "POST",
            "/api/posts",
            {"title": "Test question", "body": "What is the best way to settle a new cat at home?"},
            token=self.sara,
        )
        self.assertEqual(status, 201)
        post_id = created["post"]["id"]
        status, comment = call("POST", f"/api/posts/{post_id}/comments", {"body": "Start with one quiet room."}, token=self.sara)
        self.assertEqual(status, 201)
        status, report = call("POST", f"/api/posts/{post_id}/report", {"reason": "Moderation test"}, token=self.sara)
        self.assertEqual(status, 201)
        _, dashboard = call("GET", "/api/admin/dashboard", token=self.admin)
        self.assertTrue(any(item["post_id"] == post_id and item["status"] == "open" for item in dashboard["reports"]))
        status, _ = call("POST", f"/api/admin/posts/{post_id}/moderate", {"action": "hide"}, token=self.admin)
        self.assertEqual(status, 200)
        _, posts = call("GET", "/api/posts")
        self.assertNotIn(post_id, [item["id"] for item in posts["posts"]])
        row = self.sql("SELECT status FROM reports WHERE id = ?", (report["report"]["id"],))[0]
        self.assertEqual(row["status"], "resolved")

    def test_14_lost_adoption_and_content(self):
        status, lost = call(
            "POST",
            "/api/lost-found",
            {"kind": "found", "title": "Dog found in the test", "city": "Tanta", "species": "dog", "contact_phone": "0100"},
            token=self.sara,
        )
        self.assertEqual(status, 201)
        status, adoption = call(
            "POST",
            "/api/adoptions",
            {"title": "Cat for adoption in the test", "animal_name": "Shams", "species": "cat", "city": "Tanta"},
            token=self.sara,
        )
        self.assertEqual(status, 201)
        _, articles = call("GET", "/api/articles")
        self.assertGreaterEqual(len(articles["articles"]), 4)
        _, lost_items = call("GET", "/api/lost-found")
        self.assertIn(lost["item"]["id"], [item["id"] for item in lost_items["items"]])
        _, adoption_items = call("GET", "/api/adoptions")
        self.assertIn(adoption["item"]["id"], [item["id"] for item in adoption_items["items"]])

    def test_15_audit_log_immutable_in_database(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE audit_log SET action = 'tampered' WHERE id = 1")
            conn.rollback()
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM audit_log WHERE id = 1")
            conn.rollback()
        finally:
            conn.close()

    def test_16_admin_can_suspend_and_restore_user(self):
        status, registered = call(
            "POST",
            "/api/auth/register-customer",
            {"name": "Suspend Account", "email": "suspend@petbridge.local", "phone": "0101", "password": "Suspend123!"},
        )
        self.assertEqual(status, 201)
        user_id = registered["user"]["id"]
        token = registered["token"]
        status, _ = call("POST", f"/api/admin/users/{user_id}/status", {"status": "suspended"}, token=self.admin)
        self.assertEqual(status, 200)
        status, _ = call("GET", "/api/me", token=token)
        self.assertEqual(status, 403)
        status, _ = call("POST", "/api/auth/login", {"email": "suspend@petbridge.local", "password": "Suspend123!"})
        self.assertEqual(status, 403)
        status, _ = call("POST", f"/api/admin/users/{user_id}/status", {"status": "active"}, token=self.admin)
        self.assertEqual(status, 200)

    def test_17_commission_setting_applies_to_new_booking(self):
        status, _ = call("POST", "/api/admin/settings", {"commission_rate": 0.2}, token=self.admin)
        self.assertEqual(status, 200)
        try:
            _, directory = call("GET", "/api/directory")
            clinic = next(item for item in directory["providers"] if item["business_name"] == "Nile Veterinary Clinic")
            service = next(item for item in clinic["services"] if item["taxonomy_key"] == "vet_online")
            _, home = call("GET", "/api/client/home", token=self.sara)
            pet = home["pets"][0]
            status, created = call(
                "POST",
                "/api/bookings",
                {"service_id": service["id"], "pet_id": pet["id"], "start_at": "2030-03-01T15:00:00"},
                token=self.sara,
            )
            self.assertEqual(status, 201, created)
            self.assertEqual(created["booking"]["total"], 200)
            self.assertEqual(created["booking"]["commission"], 40)
            self.assertEqual(created["booking"]["provider_net"], 160)
        finally:
            call("POST", "/api/admin/settings", {"commission_rate": 0.12}, token=self.admin)

    def test_19_portal_pages_are_served(self):
        for path in ("/", "/login", "/provider", "/admin"):
            status, content_type, body = call_raw(path)
            self.assertEqual(status, 200, path)
            self.assertEqual(content_type, "text/html")
            self.assertIn("PetBridge", body)
            self.assertIn('lang="en"', body)

    def test_20_pwa_files_are_served(self):
        status, content_type, body = call_raw("/manifest.webmanifest")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/manifest+json")
        manifest = json.loads(body)
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "./index.html")
        status, content_type, body = call_raw("/sw.js")
        self.assertEqual(status, 200)
        self.assertIn("petbridge-shell", body)
        status, content_type, body = call_raw("/icon.svg")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "image/svg+xml")
        self.assertIn("<svg", body)

    def test_21_frontend_has_no_gradient_or_purple_template_trace(self):
        frontend = ROOT / "frontend"
        combined = ""
        for path in frontend.iterdir():
            if path.is_file():
                combined += path.read_text(encoding="utf-8").lower()
        self.assertNotIn("gradient", combined)
        self.assertNotIn("purple", combined)
        self.assertNotIn("violet", combined)

    def test_22_login_page_lists_demo_accounts_factually(self):
        _, _, body = call_raw("/login")
        for email in (
            "admin@petbridge.local",
            "sara@petbridge.local",
            "clinic@petbridge.local",
            "pending@petbridge.local",
        ):
            self.assertIn(email, body)

    def test_18_support_admin_cannot_approve(self):
        support = login("support@petbridge.local", "Support123!")
        status, _ = call(
            "POST",
            "/api/admin/approve",
            {"entity": "provider", "id": 1, "decision": "approved"},
            token=support,
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
