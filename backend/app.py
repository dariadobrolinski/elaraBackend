from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional

from backend.utils.symptoms import extract
from backend.utils.classification import classifyCondition
from backend.utils.recommender import bestPlant
from backend.utils.recipe import getRecipe

#Load environment variables if needed
from dotenv import load_dotenv
load_dotenv('.env')

class RecReq(BaseModel):
    medicalConcern: str

class PlantInfo(BaseModel):
    plantName: Optional[str]
    scientificName: Optional[str]
    medicalRating: Optional[int]
    edibleRating: Optional[int]
    edibleUses: Optional[str]
    plantImageURL: Optional[List[str]]
    plantURL: Optional[str]

class RecResp(BaseModel):
    output: Dict[str, Optional[PlantInfo]]

app = FastAPI()
@app.post("/getRecommendations", response_model=RecResp)
async def getRecommendations(req: RecReq):
    rawSymptoms = extract(req.medicalConcern)
    symptomsList = rawSymptoms["symptoms"]

    rawClasses = classifyCondition(symptomsList)
    classDict = rawClasses["outputs"]

    recs = bestPlant(classDict)

    return {"output": recs}

class RecipeReq(BaseModel):
    plantName: str
    scientificName: str
    edibleUses: str

class RecipeData(BaseModel):
    recipeName: str
    ingredients: List[str]
    instructions: str

class RecipeResp(BaseModel):
    output: RecipeData

@app.post("/getRecipe", response_model = RecipeResp)
async def recipe(req: RecipeReq):
    recipeDict = getRecipe(
        req.plantName,
        req.scientificName,
        req.edibleUses
    )

    return recipeDict