from fastapi import FastAPI, Depends, HTTPException, Request, status, Path
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime, timezone, timedelta

from utils.symptoms import extract
from utils.classification import classifyCondition
from utils.recommender import bestPlant
from utils.recipe import getRecipe

from dotenv import load_dotenv

from weasyprint import HTML
import io

from auth.hashing import Hash
from auth.oauth import getCurrentUser
from auth.jwttoken import createAccessToken
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

port = 8000
client = MongoClient(os.getenv("MONGODB_URI"), port)
db = client["User"]
savedRecipes = db["saved_recipes"]

savedRecipes.create_index(
    [("deletedAt", 1)],
    expireAfterSeconds=864000
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static_files")

templates = Jinja2Templates(directory="templates")

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

@app.post("/register")
def createUser(request: User):
    hashedPassword = Hash.bcrypt(request.password)
    userObject = dict(request)
    userObject["password"] = hashedPassword
    userID = db["users"].insert_one(userObject)
    return {"res": "created"}

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
    symptoms_dict = rawSymptoms["symptoms"]

    rawClasses = classifyCondition(symptoms_dict)
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

class RecipeJSON(BaseModel):
    symptom: str
    recipeName: str
    ingredients: List[str]
    instructions: str

@app.post("/saveRecipe")
async def saveRecipe(payload: RecipeJSON, currentUser: User = Depends(getCurrentUser)):
    doc = {
        "userId": currentUser.username,
        "symptom": payload.symptom,
        "recipe": {
            "recipeName": payload.recipeName,
            "ingredients": payload.ingredients,
            "instructions": payload.instructions
        },
        "savedAt": datetime.now(timezone.utc)
    }

    result = savedRecipes.insert_one(doc)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save recipe.")
    return {"message": "Recipe saved successfully", "id": str(result.inserted_id)}

@app.get("/getSavedRecipes")
async def getSavedRecipes(currentUser: User = Depends(getCurrentUser)):
    cursor = savedRecipes.find({
        "userId": currentUser.username,
        "deletedAt": {"$exists": False}
    }).sort("savedAt", -1)

    saved_list = []
    for doc in cursor:
        saved_list.append({
            "id": str(doc["_id"]),
            "symptom": doc.get("symptom"),
            "recipe": doc["recipe"],
            "savedAt": doc["savedAt"].isoformat()
        })

    return {"savedRecipes": saved_list}

@app.delete("/deleteRecipe/{recipe_id}")
async def deleteRecipe(
    recipe_id: str = Path(..., description="ID of the recipe to delete"),
    currentUser: User = Depends(getCurrentUser)
):
    doc = savedRecipes.find_one({
        "_id": ObjectId(recipe_id),
        "userId": currentUser.username,
        "deletedAt": {"$exists": False}
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Recipe not found or already deleted")

    result = savedRecipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": {"deletedAt": datetime.now(timezone.utc)}}
    )

    if result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to delete recipe")

    return {"message": "Recipe moved to Recently Deleted"}

@app.get("/recentlyDeleted")
async def getRecentlyDeleted(currentUser: User = Depends(getCurrentUser)):
    ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
    cursor = savedRecipes.find({
        "userId": currentUser.username,
        "deletedAt": {"$exists": True, "$gte": ten_days_ago}
    }).sort("deletedAt", -1)

    deleted_list = []
    for doc in cursor:
        deleted_list.append({
            "id": str(doc["_id"]),
            "symptom": doc.get("symptom"),
            "recipe": doc["recipe"],
            "deletedAt": doc["deletedAt"].isoformat()
        })

    return {"recentlyDeleted": deleted_list}


@app.post("/recoverRecipe/{recipe_id}")
async def recoverRecipe(
    recipe_id: str,
    currentUser: User = Depends(getCurrentUser)
):
    ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
    doc = savedRecipes.find_one({
        "_id": ObjectId(recipe_id),
        "userId": currentUser.username,
        "deletedAt": {"$exists": True, "$gte": ten_days_ago}
    })

    if not doc:
        raise HTTPException(status_code=404, detail="Recipe not found or not recoverable")

    result = savedRecipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$unset": {"deletedAt": ""}}
    )

    if result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to recover recipe")

    return {"message": "Recipe recovered successfully"}

@app.post("/downloadRecipePDF")
async def downloadRecipePDF(request: Request, payload: RecipeJSON, currentUser: User = Depends(getCurrentUser)):
    context = {
    "request": request,
    "recipe": {
        "title": payload.recipeName,
        "ingredients": payload.ingredients,
        "instructions": payload.instructions
    },
    "base_url": request.url_for("static_files", path=""),
    }
    rendered_html = templates.get_template("recipe.html").render(context)

    pdf_io = io.BytesIO()
    HTML(string=rendered_html, base_url=str(request.base_url)).write_pdf(target=pdf_io)
    pdf_io.seek(0)

    filename_safe = payload.recipeName.replace(" ", "_") + ".pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename_safe}"'
    }
    
    return StreamingResponse(pdf_io, media_type="application/pdf", headers=headers)