import os
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME")]
plants = db[os.getenv("COLL_NAME")]

def bestPlant(classDict: dict[str,str]) -> dict[str,dict]:
    recommendations = {}

    for symptom, condition in classDict.items():
        query = {
            "use_keyword": condition,          
            "Known Hazards": "None known"
        }

        sort = [
            ("medicinal_rating_search", DESCENDING),
            ("edibility_rating_search", DESCENDING)
        ]

        doc = plants.find_one(query, sort=sort)
        if doc:
            rawImages = doc.get("Image URLs", "")
            if isinstance(rawImages, str):
                imageURLs = [url.strip() for url in rawImages.split(';') if url.strip()]
            elif isinstance(rawImages, list):
                imageURLs = rawImages
            else:
                imageURLs = []
        
        doc = plants.find_one(query, sort=sort)
        if doc:
            recommendations[symptom] = { 
                "scientificName": str(doc.get("latin_name_search", "")),
                "plantName": str(doc.get("common_name_search", "")),
                "medicalRating": int(doc.get("medicinal_rating_search", 0)) if doc.get("medicinal_rating_search") is not None else 0,
                "edibleRating": int(doc.get("edibility_rating_search", 0)) if doc.get("edibility_rating_search") is not None else 0,
                "edibleUses": str(doc.get("Edible Uses", "")),
                "plantImageURL": imageURLs,
                "plantURL": str(doc.get("plant_url", ""))
            }
        else:
            recommendations[symptom] = None

    return recommendations
