import hashlib


PROFILES = {
    "dog": {
        "label": "Dog",
        "breeds": {
            "baladi": (
                "Baladi",
                "A Baladi dog known for its intelligence and how well it adapts to the Egyptian environment.",
                ["Balanced protein-rich food", "Daily walks and mental exercise", "Keep vaccinations and deworming regular"],
            ),
            "golden": (
                "Golden Retriever",
                "An active family breed that needs daily movement and regular coat care.",
                ["Daily walks and play", "Brush the coat several times a week", "Watch weight and joint health"],
            ),
            "german": (
                "German Shepherd",
                "A strong, smart breed that benefits from regular training and clear tasks.",
                ["Ongoing obedience training", "Daily physical activity", "Periodic joint checks at the vet"],
            ),
            "default": (
                "Mixed breed or unconfirmed",
                "A photo alone cannot confirm a breed, so this result is shown as a first reading.",
                ["Show the result to a vet to confirm", "Watch weight, activity and appetite", "Keep the vaccination schedule"],
            ),
        },
    },
    "cat": {
        "label": "Cat",
        "breeds": {
            "baladi": (
                "Baladi",
                "An active, adaptable Baladi cat, usually short-haired and easy to care for daily.",
                ["Clean water always available", "Short, frequent daily play", "Watch teeth and vaccinations"],
            ),
            "siamese": (
                "Siamese",
                "A social, vocal breed that loves interaction and dislikes long loneliness.",
                ["Daily play and interaction time", "A safe indoor environment", "Watch weight and teeth"],
            ),
            "persian": (
                "Persian (Shirazi)",
                "A calm long-haired breed that needs daily coat and eye care.",
                ["Daily coat brushing", "Gentle cleaning around the eyes", "Suitable food and weight watching"],
            ),
            "default": (
                "Mixed breed or unconfirmed",
                "A photo alone cannot confirm a breed, so this result is shown as a first reading.",
                ["Show the result to a vet to confirm", "Provide a clean litter box and fresh water", "Keep the vaccination schedule"],
            ),
        },
    },
    "bird": {
        "label": "Bird",
        "breeds": {
            "default": (
                "Species needs specialist confirmation",
                "Identifying a bird species from one photo needs a specialist review.",
                ["Show the photo to a bird vet", "Keep a clean cage and calm ventilation", "Offer bird-specific food, not leftovers"],
            )
        },
    },
    "other": {
        "label": "Other animal",
        "breeds": {
            "default": (
                "Species needs specialist confirmation",
                "A first reading does not replace an assessment by a vet who knows the species.",
                ["Show the result to a specialist vet", "Note eating and activity observations", "Provide a suitable, safe environment"],
            )
        },
    },
}

ALIASES = {
    "baladi": ["baladi", "بلدي"],
    "golden": ["golden", "retriever", "جولدن"],
    "german": ["german", "shepherd", "جيرمن"],
    "siamese": ["siamese", "سيامي"],
    "persian": ["persian", "shirazi", "شيرازي"],
}


def analyze_image(file_name, declared_species, image_bytes=b""):
    species = declared_species if declared_species in PROFILES else "other"
    profile = PROFILES[species]
    search_text = (file_name or "").lower()
    breed_key = "default"
    for key, words in ALIASES.items():
        if any(word in search_text for word in words):
            if key in profile["breeds"]:
                breed_key = key
                break
    if breed_key == "default" and image_bytes:
        digest = hashlib.sha256(image_bytes).hexdigest()
        candidates = list(profile["breeds"].keys())
        breed_key = candidates[int(digest[:4], 16) % len(candidates)]
    breed, summary, care = profile["breeds"].get(
        breed_key, profile["breeds"]["default"]
    )
    return {
        "beta": True,
        "label": "Demo analysis for display",
        "species": profile["label"],
        "species_key": species,
        "breed": breed,
        "summary": summary,
        "care": care,
        "note": "This is a demo result from a local display flow and carries no accuracy rate. Confirming breed and health needs a vet, or a real vision model at launch.",
        "engine": "local-demo-v1",
    }
