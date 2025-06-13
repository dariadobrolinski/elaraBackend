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
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
pendingUsers = db["pending_users"]  # New collection for unverified users

savedRecipes.create_index(
    [("deletedAt", 1)],
    expireAfterSeconds=864000
)

# Create TTL index for pending users - expire after 24 hours
pendingUsers.create_index(
    [("verification_token_expires", 1)],
    expireAfterSeconds=0
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
    email: str
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

class EmailVerificationRequest(BaseModel):
    email: str

class EmailVerificationToken(BaseModel):
    token: str

@app.get("/")
def readRoot(currentUser: User = Depends(getCurrentUser)):
    return {"data": "Welcome to Elara"}

def send_verification_email(email: str, username: str, token: str):
    """Send verification email to user"""
    try:
        smtp_server = os.getenv("SMTP_SERVER", "mail.privateemail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_login = os.getenv("SMTP_LOGIN", "edward@edwardgaibor.me")
        smtp_username = "edward@edwardgaibor.me"
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_username or not smtp_password:
            print("Warning: Email service not configured properly")
            return False  # Don't raise exception, just return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = "Verify Your Elara Account"
        
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        verification_link = f"{frontend_url}/verify-email?token={token}&email={email}"
        
        body = f"""
        <html>
        <body>
            <h2>Welcome to Elara, {username}!</h2>
            <p>Thank you for registering with Elara. To complete your registration, please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}" style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Verify Email Address</a></p>
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p>{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with Elara, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The Elara Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_login, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.post("/register")
def createUser(request: User):
    try:
        print(f"Registration attempt for email: {request.email}, username: {request.username}")
        
        # Check if user already exists in main users collection
        existing_user = db["users"].find_one({"$or": [{"username": request.username}, {"email": request.email}]})
        if existing_user:
            if existing_user.get("email") == request.email:
                raise HTTPException(status_code=400, detail="Email already registered")
            else:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Check if user already exists in pending users collection
        existing_pending = pendingUsers.find_one({"$or": [{"username": request.username}, {"email": request.email}]})
        if existing_pending:
            if existing_pending.get("email") == request.email:
                raise HTTPException(status_code=400, detail="Email already registered. Please check your email for verification instructions.")
            else:
                raise HTTPException(status_code=400, detail="Username already taken")
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate password length
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Validate username
        if len(request.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
        
        hashedPassword = Hash.bcrypt(request.password)
        verification_token = secrets.token_urlsafe(32)
        
        # Store in pending users collection instead of main users collection
        pendingUserObject = {
            "email": request.email,
            "username": request.username,
            "password": hashedPassword,
            "verification_token": verification_token,
            "verification_token_expires": datetime.now(timezone.utc) + timedelta(hours=24),
            "created_at": datetime.now(timezone.utc)
        }
        
        # Insert into pending users collection
        pendingUserID = pendingUsers.insert_one(pendingUserObject)
        print(f"Pending user created with ID: {pendingUserID.inserted_id}")
        
        # Send verification email
        email_sent = send_verification_email(request.email, request.username, verification_token)
        
        if not email_sent:
            # If email fails, remove the pending user
            pendingUsers.delete_one({"_id": pendingUserID.inserted_id})
            raise HTTPException(status_code=500, detail="Failed to send verification email. Please try again.")
        
        return {"message": "Registration successful! Please check your email and click the verification link to complete your account setup."}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/verify-email")
def verifyEmail(request: EmailVerificationToken):
    # Look for user in pending users collection
    pending_user = pendingUsers.find_one({
        "verification_token": request.token,
        "verification_token_expires": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not pending_user:
        # Check if token exists but is expired
        expired_user = pendingUsers.find_one({"verification_token": request.token})
        if expired_user:
            raise HTTPException(status_code=410, detail="Verification token has expired. Please register again.")
        else:
            raise HTTPException(status_code=400, detail="Invalid verification token")
    
    # Create verified user object for main users collection
    verified_user = {
        "email": pending_user["email"],
        "username": pending_user["username"],
        "password": pending_user["password"],
        "email_verified": True,
        "created_at": pending_user["created_at"],
        "verified_at": datetime.now(timezone.utc)
    }
    
    # Insert into main users collection
    user_result = db["users"].insert_one(verified_user)
    
    if user_result.inserted_id:
        # Remove from pending users collection
        pendingUsers.delete_one({"_id": pending_user["_id"]})
        print(f"User {pending_user['username']} successfully verified and moved to main collection")
    else:
        raise HTTPException(status_code=500, detail="Failed to create verified user account")
    
    return {"message": "Email verified successfully! Your account is now active and you can log in."}

@app.post("/get-email-for-username")
def getEmailForUsername(request: Dict[str, str]):
    username = request.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    # Check pending users first
    pending_user = pendingUsers.find_one({"username": username})
    if pending_user:
        # Mask email for privacy
        email = pending_user["email"]
        parts = email.split("@")
        if len(parts[0]) > 2:
            masked_email = parts[0][0] + "*" * (len(parts[0]) - 2) + parts[0][-1] + "@" + parts[1]
        else:
            masked_email = parts[0][0] + "*@" + parts[1]
        return {"email": email, "masked_email": masked_email}
    
    raise HTTPException(status_code=404, detail="Username not found")

@app.post("/resend-verification")
def resendVerification(request: EmailVerificationRequest):
    # Check both pending and main users collections
    pending_user = pendingUsers.find_one({"email": request.email})
    main_user = db["users"].find_one({"email": request.email})
    
    if main_user and main_user.get("email_verified", False):
        raise HTTPException(status_code=400, detail="Email already verified. You can log in now.")
    
    if not pending_user:
        raise HTTPException(status_code=404, detail="No pending registration found for this email. Please register again.")
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    
    pendingUsers.update_one(
        {"_id": pending_user["_id"]},
        {
            "$set": {
                "verification_token": verification_token,
                "verification_token_expires": datetime.now(timezone.utc) + timedelta(hours=24)
            }
        }
    )
    
    # Send verification email
    email_sent = send_verification_email(request.email, pending_user["username"], verification_token)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    return {"message": "Verification email sent successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db["users"].find_one({"username": form_data.username})

    if not user:
        # Check if user exists in pending collection
        pending_user = pendingUsers.find_one({"username": form_data.username})
        if pending_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email address to complete registration before logging in"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    # User exists in main collection, they should be verified
    if not user.get("email_verified", False):
        # This shouldn't happen with new flow, but keep as safety check
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account verification incomplete. Please contact support."
        )
    
    if not Hash.verify(user["password"], form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    accessToken = createAccessToken(data={"sub": user["username"]})
    return {"access_token": accessToken, "token_type": "bearer"}

@app.post("/getRecommendations", response_model=RecResp)
async def getRecommendations(req: RecReq, currentUser: User = Depends(getCurrentUser)):
    rawSymptoms = extract(req.medicalConcern)
    symptoms_dict = rawSymptoms["symptoms"]

    rawClasses = classifyCondition(symptoms_dict)
    classDict = rawClasses["outputs"]

    recs = bestPlant(classDict)

    return {"output": recs}

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