import os
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

uri  = os.environ["MONGODB_URI"]
db   = os.environ.get("DB_NAME",  "ai_in_action")
coll = os.environ.get("COLL_NAME","pfaf_plants")

client = MongoClient(uri)
plants = client[db][coll]

csv_path = os.path.join(os.path.dirname(__file__), "data\pfaf_plants_merged_2.csv")
df = pd.read_csv(csv_path)

docs = df.to_dict(orient="records")

BATCH = 1000
for i in tqdm(range(0, len(docs), BATCH), desc="Uploading"):
    plants.insert_many(docs[i:i+BATCH])

plants.create_index([("uses", ASCENDING)])
plants.create_index([("medicinal_rating", DESCENDING),
                     ("edibility_rating",  DESCENDING)])
plants.create_index([("hazards", ASCENDING)], sparse=True)

print(f"✅ Imported {len(docs):,} documents into {db}.{coll}")
