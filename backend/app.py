from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional

from utils.symptoms import extract
from utils.classification import classifyCondition
from utils.recommender import bestPlant
from utils.recipe import getRecipe

#Load environment variables if needed
from dotenv import load_dotenv
load_dotenv('.env')

from weasyprint import HTML
import io

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static_files")

templates = Jinja2Templates(directory="templates")

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
async def getRecommendations(req: RecReq):
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
async def recipe(req: RecipeReq):
    recipeDict = getRecipe(
        req.plantName,
        req.scientificName,
        req.edibleUses
    )

    return recipeDict

class RecipeJSON(BaseModel):
    recipeName: str
    ingredients: List[str]
    instructions: str

@app.post("/downloadRecipePDF")
async def downloadRecipePDF(request: Request, payload: RecipeJSON):
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