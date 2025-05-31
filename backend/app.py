from fastapi import FastAPI, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from pymongo import MongoClient
import os

from utils.symptoms import extract
from utils.classification import classifyCondition
from utils.recommender import bestPlant
from utils.recipe import getRecipe

from dotenv import load_dotenv
load_dotenv('.env')

port = 8000
client = MongoClient(os.getenv("MONGODB_URI"), port)
db = client["User"]

from auth.hashing import Hash
from auth.oauth import getCurrentUser
from auth.jwttoken import createAccessToken
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
class User(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    accessToken: str
    tokenType: str

class TokenData(BaseModel):
    username: Optional[str] = None

@app.get("/")
def readRoot(currentUser: User = Depends(getCurrentUser)):
    return {"data": "Welcome to Elara"}

# @app.post("/register")
# def createUser(request: User):
#     hashedPassword = Hash.bcrypt(request.password)
#     userObject = dict(request)
#     userObject["password"] = hashedPassword
#     userID = db["users"].insert_one(userObject)
#     return {"res": "created"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db["users"].find_one({"username": form_data.username})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not Hash.verify(user["password"], form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    accessToken = createAccessToken(data={"sub": user["username"]})
    return {"access_token": accessToken, "token_type": "bearer"}

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

@app.post("/getRecommendations", response_model=RecResp)
async def getRecommendations(req: RecReq, currentUser: User = Depends(getCurrentUser)):
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
async def recipe(req: RecipeReq, currentUser: User = Depends(getCurrentUser)):
    recipeDict = getRecipe(
        req.plantName,
        req.scientificName,
        req.edibleUses
    )

    return recipeDict