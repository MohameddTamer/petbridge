import json
from datetime import date, timedelta

from breed import analyze_image
from db import audit, hash_password, now_iso
from taxonomy import SERVICE_INDEX


def d(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def add_user(conn, name, email, phone, password, role, admin_level=""):
    digest, salt = hash_password(password)
    cur = conn.execute(
        """
        INSERT INTO users(name, email, phone, password_hash, salt, role, admin_level, status, created_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """,
        (name, email, phone, digest, salt, role, admin_level, now_iso()),
    )
    return cur.lastrowid


def add_provider(conn, user_id, business, kind, description, city, area, address, phone, status="approved", plan="pro"):
    cur = conn.execute(
        """
        INSERT INTO providers(user_id, business_name, kind, description, city, area, address, phone, status, plan, created_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, business, kind, description, city, area, address, phone, status, plan, now_iso()),
    )
    provider_id = cur.lastrowid
    docs = [
        ("national_id", "Owner national ID", "owner-id.pdf"),
        ("license", "Business licence", "business-license.pdf"),
    ]
    for doc_type, label, file_name in docs:
        conn.execute(
            """
            INSERT INTO provider_documents(provider_id, doc_type, label, file_name, status, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                provider_id,
                doc_type,
                label,
                file_name,
                "approved" if status == "approved" else "pending",
                now_iso(),
            ),
        )
    return provider_id


def add_service(conn, provider_id, taxonomy_key, price, duration=60, mode="onsite", status="approved"):
    info = SERVICE_INDEX[taxonomy_key]
    cur = conn.execute(
        """
        INSERT INTO services(provider_id, taxonomy_key, name, category, price, duration_min, mode, status, created_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            provider_id,
            taxonomy_key,
            info["label"],
            info["category"],
            price,
            duration,
            mode,
            status,
            now_iso(),
        ),
    )
    return cur.lastrowid


def add_slot(conn, provider_id, service_id, day_offset, start, end, capacity=3):
    cur = conn.execute(
        """
        INSERT INTO availability(provider_id, service_id, date, start_time, end_time, capacity, active, created_at)
        VALUES(?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (provider_id, service_id, d(day_offset), start, end, capacity, now_iso()),
    )
    return cur.lastrowid


def add_booking(conn, customer_id, provider_id, service_id, pet_id, slot_id, start_at, status, total, rate=0.12, payment="simulated_paid"):
    commission = round(total * rate, 2)
    net = round(total - commission, 2)
    cur = conn.execute(
        """
        INSERT INTO bookings(customer_id, provider_id, service_id, pet_id, slot_id, start_at, status, total,
                             commission_rate, commission, provider_net, payment_status, created_at, updated_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            provider_id,
            service_id,
            pet_id,
            slot_id,
            start_at,
            status,
            total,
            rate,
            commission,
            net,
            payment,
            now_iso(),
            now_iso(),
        ),
    )
    return cur.lastrowid


def seed_all(conn):
    admin_id = add_user(
        conn, "PetBridge Admin", "admin@petbridge.local", "01000000000", "Admin123!", "admin", "super_admin"
    )
    mod_id = add_user(
        conn, "Content Moderator", "mod@petbridge.local", "01000000001", "Mod12345!", "admin", "moderator"
    )
    add_user(
        conn, "Support Team", "support@petbridge.local", "01000000002", "Support123!", "admin", "support"
    )

    sara = add_user(conn, "Sara Mahmoud", "sara@petbridge.local", "01012345678", "Sara123!", "customer")
    omar = add_user(conn, "Omar El Shazly", "omar@petbridge.local", "01023456789", "Omar123!", "customer")
    mariam = add_user(conn, "Mariam Adel", "mariam@petbridge.local", "01034567890", "Mariam123!", "customer")

    clinic_user = add_user(conn, "Dr. Karim Samy", "clinic@petbridge.local", "01098765432", "Vet123!", "provider")
    clinic = add_provider(
        conn,
        clinic_user,
        "Nile Veterinary Clinic",
        "vet",
        "A full-service clinic in Tanta for checkups, vaccinations and surgery, with emergency cover until midnight.",
        "Tanta",
        "El Bahr Street",
        "12 El Bahr Street, Tanta",
        "01098765432",
    )
    groom_user = add_user(conn, "Mona Adel", "groom@petbridge.local", "01087654321", "Groom123!", "provider")
    groom = add_provider(
        conn,
        groom_user,
        "Warda Pet Salon",
        "grooming",
        "Calm grooming and care for dogs and cats in Cairo, with mobile visits across Nasr City and Heliopolis.",
        "Cairo",
        "Nasr City",
        "45 Abbas El Akkad Street, Nasr City",
        "01087654321",
    )
    train_user = add_user(conn, "Ahmed Rizk", "train@petbridge.local", "01076543210", "Train123!", "provider")
    trainer = add_provider(
        conn,
        train_user,
        "Rizk Dog Training Academy",
        "training",
        "Obedience training and behaviour work with written plans and a progress report after every session.",
        "Alexandria",
        "Smouha",
        "8 Fawzy Moaz Street, Smouha",
        "01076543210",
    )
    hotel_user = add_user(conn, "Heba Nour", "hotel@petbridge.local", "01065432109", "Hotel123!", "provider")
    hotel = add_provider(
        conn,
        hotel_user,
        "Heba's Pet House",
        "boarding",
        "Overnight boarding and day care in Tanta with a daily report, photos and outdoor play time.",
        "Tanta",
        "El Galaa",
        "3 El Galaa Street, Tanta",
        "01065432109",
    )
    shop_user = add_user(conn, "Animal World Shop", "shop@petbridge.local", "01054321098", "Shop123!", "provider")
    shop = add_provider(
        conn,
        shop_user,
        "Animal World Supplies",
        "shops",
        "A supplies shop in Cairo delivering food and licensed veterinary medicine the same day.",
        "Cairo",
        "Maadi",
        "9 Street 9, Maadi",
        "01054321098",
    )
    move_user = add_user(conn, "Youssef Hamdy", "move@petbridge.local", "01043210987", "Move123!", "provider")
    transport = add_provider(
        conn,
        move_user,
        "Safe Pet Transport",
        "transport",
        "Air-conditioned pet transport inside the city and between governorates, in secure crates with updates during the trip.",
        "Alexandria",
        "Sidi Gaber",
        "21 El Geish Road, Sidi Gaber",
        "01043210987",
    )
    shelter_user = add_user(conn, "Rahma Association", "shelter@petbridge.local", "01032109876", "Shelter123!", "provider")
    shelter = add_provider(
        conn,
        shelter_user,
        "Rahma Animal Rescue Shelter",
        "rescue_breeding",
        "A shelter in Tanta running responsible adoption, temporary fostering and neutering campaigns.",
        "Tanta",
        "El Agizy",
        "El Agizy Road, Tanta",
        "01032109876",
    )
    photo_user = add_user(conn, "Layan Photography", "photo@petbridge.local", "01021098765", "Photo123!", "provider")
    photo = add_provider(
        conn,
        photo_user,
        "Layan Pet Photography",
        "extra",
        "Calm pet photo sessions in the studio or at home, across Cairo.",
        "Cairo",
        "Zamalek",
        "5 Brazil Street, Zamalek",
        "01021098765",
    )
    pending_user = add_user(conn, "El Baraka Clinic", "pending@petbridge.local", "01011112222", "Wait123!", "provider")
    pending = add_provider(
        conn,
        pending_user,
        "El Baraka New Veterinary Clinic",
        "vet",
        "A clinic in Alexandria awaiting document review before it appears to customers.",
        "Alexandria",
        "Moharam Bek",
        "17 Moharam Bek Street",
        "01011112222",
        status="pending",
        plan="basic",
    )

    service_rows = {}
    service_rows["clinic_vaccine"] = add_service(conn, clinic, "vet_vaccine", 350, 30)
    service_rows["clinic_general"] = add_service(conn, clinic, "vet_general", 250, 45)
    service_rows["clinic_online"] = add_service(conn, clinic, "vet_online", 200, 30, "online")
    service_rows["clinic_emergency"] = add_service(conn, clinic, "vet_emergency", 500, 60)
    service_rows["groom_full"] = add_service(conn, groom, "groom_full", 450, 90)
    service_rows["groom_mobile"] = add_service(conn, groom, "groom_mobile", 650, 90, "home")
    service_rows["train_obedience"] = add_service(conn, trainer, "train_obedience", 800, 60)
    service_rows["train_behavior"] = add_service(conn, trainer, "train_behavior", 950, 75)
    service_rows["hotel_night"] = add_service(conn, hotel, "board_hotel", 300, 1440)
    service_rows["hotel_daycare"] = add_service(conn, hotel, "board_daycare", 180, 600)
    service_rows["shop_delivery"] = add_service(conn, shop, "shop_delivery", 60, 30, "delivery")
    service_rows["shop_food_plan"] = add_service(conn, shop, "shop_food_plan", 1200, 30, "delivery")
    service_rows["transport_local"] = add_service(conn, transport, "transport_local", 280, 120, "home")
    service_rows["shelter_adoption"] = add_service(conn, shelter, "rescue_adoption", 0, 45)
    service_rows["photo_session"] = add_service(conn, photo, "extra_photo", 700, 120)
    add_service(conn, pending, "vet_general", 220, 45, status="pending")

    slots = {}
    slots["vaccine"] = add_slot(conn, clinic, service_rows["clinic_vaccine"], 2, "10:00", "10:30", 4)
    slots["general"] = add_slot(conn, clinic, service_rows["clinic_general"], 1, "12:00", "12:45", 3)
    slots["groom"] = add_slot(conn, groom, service_rows["groom_full"], 3, "11:00", "12:30", 2)
    slots["hotel"] = add_slot(conn, hotel, service_rows["hotel_night"], 4, "09:00", "10:00", 5)
    add_slot(conn, clinic, service_rows["clinic_online"], 2, "18:00", "18:30", 3)
    add_slot(conn, clinic, service_rows["clinic_emergency"], 1, "20:00", "21:00", 2)
    add_slot(conn, groom, service_rows["groom_mobile"], 4, "10:00", "11:30", 1)
    add_slot(conn, trainer, service_rows["train_obedience"], 6, "17:00", "18:00", 2)
    add_slot(conn, shop, service_rows["shop_delivery"], 1, "09:00", "21:00", 20)
    add_slot(conn, transport, service_rows["transport_local"], 2, "08:00", "10:00", 2)
    add_slot(conn, shelter, service_rows["shelter_adoption"], 3, "11:00", "11:45", 4)
    add_slot(conn, photo, service_rows["photo_session"], 7, "13:00", "15:00", 1)

    pets = {}
    pet_rows = [
        (sara, "Rocky", "dog", "Baladi", -900, "Male", 18.5, "Sensitive to chicken"),
        (sara, "Lulu", "cat", "Persian", -500, "Female", 4.2, ""),
        (omar, "Max", "dog", "German Shepherd", -1100, "Male", 31.0, ""),
        (mariam, "Simsim", "cat", "Baladi", -260, "Male", 3.8, ""),
        (mariam, "Bella", "dog", "Golden Retriever", -720, "Female", 25.4, ""),
        (omar, "Kiwi", "bird", "Cockatiel", -400, "Male", 0.09, ""),
    ]
    for owner, name, species, breed, born_offset, sex, weight, notes in pet_rows:
        cur = conn.execute(
            """
            INSERT INTO pets(owner_id, name, species, breed, birth_date, sex, weight_kg, notes, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (owner, name, species, breed, d(born_offset), sex, weight, notes, now_iso()),
        )
        pets[name] = cur.lastrowid

    health_rows = [
        (pets["Rocky"], "vaccination", "Rabies vaccination", -370, -5, "Nile Veterinary Clinic", "The yearly dose is overdue"),
        (pets["Rocky"], "medication", "Deworming treatment", -80, 10, "Nile Veterinary Clinic", ""),
        (pets["Lulu"], "vaccination", "Quadruple vaccination", -180, 25, "Nile Veterinary Clinic", ""),
        (pets["Max"], "vaccination", "Eight-in-one vaccination", -300, 40, "El Borg Veterinary Clinic", ""),
        (pets["Simsim"], "checkup", "Dental checkup", -40, 140, "", ""),
        (pets["Bella"], "medication", "Joint supplement", -20, 6, "", "One tablet daily with food"),
    ]
    for pet_id, kind, name, given, due, provider_name, notes in health_rows:
        conn.execute(
            """
            INSERT INTO health_records(pet_id, kind, name, given_date, next_due, provider_name, notes, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pet_id, kind, name, d(given), d(due) if due is not None else None, provider_name, notes, now_iso()),
        )

    completed = add_booking(
        conn,
        sara,
        clinic,
        service_rows["clinic_general"],
        pets["Rocky"],
        slots["general"],
        d(-2) + "T12:00:00",
        "completed",
        500,
    )
    add_booking(
        conn,
        omar,
        trainer,
        service_rows["train_obedience"],
        pets["Max"],
        None,
        d(5) + "T17:00:00",
        "accepted",
        800,
    )
    add_booking(
        conn,
        mariam,
        hotel,
        service_rows["hotel_night"],
        pets["Bella"],
        slots["hotel"],
        d(4) + "T09:00:00",
        "pending",
        300,
    )
    add_booking(
        conn,
        sara,
        groom,
        service_rows["groom_full"],
        pets["Lulu"],
        slots["groom"],
        d(3) + "T11:00:00",
        "proposed",
        450,
    )
    add_booking(
        conn,
        omar,
        clinic,
        service_rows["clinic_emergency"],
        pets["Max"],
        None,
        d(-10) + "T21:00:00",
        "cancelled",
        500,
    )

    reviews = [
        (sara, clinic, completed, 5, "The checkup was organised and the doctor explained everything calmly."),
        (omar, trainer, None, 5, "The training plan is clear and there is follow-up after the session."),
        (mariam, hotel, None, 4, "The daily report and photos reassured me through the whole stay."),
        (sara, groom, None, 5, "Calm handling, and the cat came out clean and unstressed."),
    ]
    for customer_id, provider_id, booking_id, rating, text in reviews:
        conn.execute(
            """
            INSERT INTO reviews(customer_id, provider_id, booking_id, rating, text, created_at)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (customer_id, provider_id, booking_id, rating, text, now_iso()),
        )

    post_one = conn.execute(
        "INSERT INTO posts(author_id, title, body, status, created_at) VALUES(?, ?, ?, 'visible', ?)",
        (sara, "How do I get my dog used to car rides?", "Rocky gets very anxious in the car. What did you try that actually worked?", now_iso()),
    ).lastrowid
    conn.execute(
        "INSERT INTO comments(post_id, author_id, body, created_at) VALUES(?, ?, ?, ?)",
        (post_one, omar, "Start with very short trips and reward him after each one.", now_iso()),
    )
    conn.execute(
        "INSERT INTO posts(author_id, title, body, status, created_at) VALUES(?, ?, ?, 'visible', ?)",
        (mariam, "Suitable food for a cat with allergies?", "Simsim has recurring allergies and I need experiences with medical food.", now_iso()),
    )
    hidden_post = conn.execute(
        "INSERT INTO posts(author_id, title, body, status, created_at) VALUES(?, ?, ?, 'visible', ?)",
        (omar, "External offer", "Reported content that breaks the rules, waiting for moderation review.", now_iso()),
    ).lastrowid
    conn.execute(
        "INSERT INTO reports(reporter_id, post_id, reason, status, created_at) VALUES(?, ?, ?, 'open', ?)",
        (sara, hidden_post, "Off-platform advertising", now_iso()),
    )

    lost_rows = [
        (sara, "lost", "Baladi dog lost in Tanta", "Rocky left the house wearing a green collar.", "Rocky", "dog", "Tanta", "El Bahr Street", "01012345678"),
        (omar, "found", "Small cat found in Smouha", "A small friendly cat found near Fawzy Moaz Street.", "", "cat", "Alexandria", "Smouha", "01023456789"),
        (mariam, "lost", "Cat lost in Nasr City", "Simsim is grey with green eyes.", "Simsim", "cat", "Cairo", "Nasr City", "01034567890"),
    ]
    for row in lost_rows:
        conn.execute(
            """
            INSERT INTO lost_found(author_id, kind, title, description, pet_name, species, city, area, contact_phone, status, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (*row, now_iso()),
        )

    adoption_rows = [
        (shelter, "Small cat ready for adoption", "Filfil", "cat", "Baladi", "3 months", "Tanta", "Filfil has had his first vaccination and uses the litter box."),
        (sarah := sara, "Baladi puppy looking for a home", "Bondoq", "dog", "Baladi", "5 months", "Tanta", "Bondoq is sociable and needs a home with time for play and training."),
        (shelter, "Calm cat for adoption", "Warda", "cat", "Persian mix", "1 year", "Tanta", "Warda is neutered, calm and suited to an apartment."),
    ]
    for row in adoption_rows:
        conn.execute(
            """
            INSERT INTO adoptions(author_id, title, animal_name, species, breed, age_label, city, description, contact_phone, status, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, '01000000003', 'available', ?)
            """,
            (*row, now_iso()),
        )

    articles = [
        ("Dog vaccination schedule in the first year", "Health", "A practical guide to core vaccination dates and booster doses.", "The first year of a dog's life matters most for building immunity. Start with the eight-in-one doses in the first weeks, then the rabies dose on schedule, and record every dose in the pet's file with its next due date. Do not delay boosters, and ask the vet before any vaccination if the dog is ill or on medication.", "Dr. Karim Samy"),
        ("Feeding cats at home without mistakes", "Nutrition", "The key rules for safe, balanced cat meals.", "A cat needs animal protein as a staple and cannot live on starches alone. Avoid onion, garlic, grapes and chocolate completely, and keep clean water available all day. Change food gradually over a week so digestion is not upset.", "Dr. Sara Nabil"),
        ("The first week with an adopted dog", "Adoption and training", "Calm steps that help the new animal feel safe.", "Prepare a fixed place for sleeping, water and food before the dog arrives. In the first days keep visits and noise low, and start a simple routine for walks and meals. Do not punish fear; reward calm behaviour and give the relationship its natural time.", "Ahmed Rizk"),
        ("Signs that need a vet immediately", "Emergency", "Symptoms that cannot wait until tomorrow.", "Difficulty breathing, severe lethargy, repeated vomiting with blood, not urinating, or swallowing a foreign object are all emergency signs. Never give human medicine to an animal, and keep the number of the nearest emergency clinic in your phone.", "Dr. Karim Samy"),
    ]
    for title, category, excerpt, body, author in articles:
        conn.execute(
            "INSERT INTO articles(title, category, excerpt, body, author, created_at) VALUES(?, ?, ?, ?, ?, ?)",
            (title, category, excerpt, body, author, now_iso()),
        )

    products = [
        (shop, "Dry food for adult dogs, 10 kg", "A balanced formula for medium-activity dogs.", 1450, 24),
        (shop, "Wet cat food, 400 g tin", "A protein-rich meal for adult cats.", 85, 120),
        (shop, "Clumping cat litter, 5 litres", "Fast-clumping litter with good odour control.", 210, 40),
        (shop, "Gentle shampoo for sensitive skin", "A mild formula for regular baths.", 175, 32),
        (shop, "Cotton rope toy", "A durable toy for safe interactive play.", 95, 55),
        (shop, "Medium transport crate", "A ventilated crate with a secure lock for short trips.", 620, 12),
    ]
    product_ids = []
    for provider_id, name, desc, price, stock in products:
        cur = conn.execute(
            """
            INSERT INTO products(provider_id, name, description, price, stock, status, created_at)
            VALUES(?, ?, ?, ?, ?, 'approved', ?)
            """,
            (provider_id, name, desc, price, stock, now_iso()),
        )
        product_ids.append(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO products(provider_id, name, description, price, stock, status, created_at)
        VALUES(?, 'Decorated leather collar', 'A new product waiting for admin approval.', 240, 15, 'pending', ?)
        """,
        (shop, now_iso()),
    )

    order_total = 170.0
    order_rate = 0.10
    conn.execute(
        """
        INSERT INTO orders(customer_id, provider_id, product_id, qty, total, commission_rate, commission, provider_net,
                           payment_status, status, created_at)
        VALUES(?, ?, ?, 2, ?, ?, ?, ?, 'simulated_paid', 'placed', ?)
        """,
        (
            sara,
            shop,
            product_ids[1],
            order_total,
            order_rate,
            round(order_total * order_rate, 2),
            round(order_total * (1 - order_rate), 2),
            now_iso(),
        ),
    )

    result = analyze_image("roki-baladi.jpg", "dog", b"seed-demo-image")
    conn.execute(
        """
        INSERT INTO breed_analyses(user_id, pet_id, file_name, declared_species, result_json, created_at)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (sara, pets["Rocky"], "roki-baladi.jpg", "dog", json.dumps(result, ensure_ascii=False), now_iso()),
    )

    actor = {"id": admin_id, "role": "admin"}
    audit(conn, actor, "seed_initialized", "system", None, "Seed data created")
    conn.commit()
