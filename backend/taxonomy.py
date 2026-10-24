CATEGORIES = [
    {
        "key": "vet",
        "label": "Vets and veterinary clinics",
        "services": [
            ("vet_general", "General and specialist checkup"),
            ("vet_vaccine", "Vaccinations and parasite prevention"),
            ("vet_surgery", "Surgery and neutering"),
            ("vet_lab", "Lab tests, X-ray and ultrasound"),
            ("vet_emergency", "24-hour veterinary emergency"),
            ("vet_home", "Home vet visit"),
            ("vet_online", "Online vet consultation"),
            ("vet_microchip", "Microchip implant"),
            ("vet_rehab", "Physiotherapy and rehabilitation"),
        ],
    },
    {
        "key": "grooming",
        "label": "Grooming and care",
        "services": [
            ("groom_full", "Bath, cut and de-matting"),
            ("groom_nails", "Nail trim, ear and gland cleaning"),
            ("groom_medical_bath", "Medicated bath for skin and allergies"),
            ("groom_mobile", "Mobile grooming at home"),
        ],
    },
    {
        "key": "training",
        "label": "Training and behaviour",
        "services": [
            ("train_obedience", "Basic and advanced obedience training"),
            ("train_behavior", "Behaviour correction"),
            ("train_puppy_guard", "Puppy, protection and guard training"),
            ("train_home", "Training at the customer's home"),
            ("train_course", "Video training course"),
        ],
    },
    {
        "key": "boarding",
        "label": "Boarding and care",
        "services": [
            ("board_hotel", "Hotel and overnight boarding"),
            ("board_daycare", "Day care"),
            ("board_sitter", "Pet sitter at the customer's home"),
            ("board_walking", "Solo or group dog walking"),
        ],
    },
    {
        "key": "shops",
        "label": "Shops and suppliers",
        "services": [
            ("shop_delivery", "Food and supplies with delivery"),
            ("shop_pharmacy", "Veterinary pharmacy"),
            ("shop_food_plan", "Monthly food subscription and medical food"),
            ("shop_animals_gear", "Animals, accessories, cages and tanks"),
        ],
    },
    {
        "key": "transport",
        "label": "Transport and travel",
        "services": [
            ("transport_local", "Pet transport in-city and between cities"),
            ("transport_international", "International transport and travel papers"),
        ],
    },
    {
        "key": "rescue_breeding",
        "label": "Shelters and breeders",
        "services": [
            ("rescue_adoption", "Adoption listings and shelter request management"),
            ("breeder_verified", "Verified breeder with a health file"),
            ("breeding_match", "Documented mating with health files for both sides"),
        ],
    },
    {
        "key": "extra",
        "label": "Extra services",
        "services": [
            ("extra_photo", "Professional pet photography"),
            ("extra_events", "Pets at events"),
            ("extra_aftercare", "Burial and aftercare"),
            ("extra_nutrition", "Nutrition consultation and custom meal plan"),
        ],
    },
]

SERVICE_INDEX = {}
for category in CATEGORIES:
    for service_key, service_label in category["services"]:
        SERVICE_INDEX[service_key] = {
            "key": service_key,
            "label": service_label,
            "category": category["key"],
            "category_label": category["label"],
        }


def taxonomy_payload():
    categories = []
    for category in CATEGORIES:
        categories.append(
            {
                "key": category["key"],
                "label": category["label"],
                "services": [
                    {"key": key, "label": label} for key, label in category["services"]
                ],
            }
        )
    return {"categories": categories, "service_count": len(SERVICE_INDEX)}
