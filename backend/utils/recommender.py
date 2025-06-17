import os
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME")]
plants = db[os.getenv("COLL_NAME")]

def bestPlant(classDict: dict[str, str], edible: bool = False) -> dict[str, list[dict]]:
    recommendations: dict[str, list[dict]] = {}

    primary   = "edibility_rating_search"   if edible else "medicinal_rating_search"
    secondary = "medicinal_rating_search"   if edible else "edibility_rating_search"

    for symptom, condition in classDict.items():
        query = {
            "use_keyword": condition,
            "Known Hazards": "None known"
        }

        sort_criteria = [
            (primary,   DESCENDING),
            (secondary, DESCENDING)
        ]

        cursor = plants.find(query).sort(sort_criteria).limit(3)
        topPlants: list[dict] = []

        for doc in cursor:
            raw_images = doc.get("Image URLs", "")
            if isinstance(raw_images, str):
                imageURLs = [u.strip() for u in raw_images.split(";") if u.strip()]
            elif isinstance(raw_images, list):
                imageURLs = raw_images
            else:
                imageURLs = []

            topPlants.append({
                "plantName":      str(doc.get("common_name_search", "")),
                "scientificName": str(doc.get("latin_name_search", "")),
                "medicalRating":  int(doc.get("medicinal_rating_search") or 0),
                "edibleRating":   int(doc.get("edibility_rating_search") or 0),
                "edibleUses":     str(doc.get("Edible Uses", "")),
                "plantImageURL":  imageURLs,
                "plantURL":       str(doc.get("plant_url", ""))
            })

        recommendations[symptom] = topPlants

    return recommendations
