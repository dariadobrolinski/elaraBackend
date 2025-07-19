# Elara AI
<img width="1500" height="500" alt="Elara AI Repo Banner" src="https://github.com/user-attachments/assets/9acc35fb-dcc7-403b-9404-7b2d0c03d07c" />

🏆 **3rd Place Winner - MongoDB Track - ![AI in Action 2025 Hackathon](https://devpost.com/software/elara-x47age)** 🏆

#### This repo only contains the backend, find the front end here: 
[![Screenshot 2025-06-06 090439](https://github.com/user-attachments/assets/776ac3fd-4ea4-4699-99eb-35cc47c78017)](https://github.com/gaiborjosue/elaraFrontend)


## 📚 Table of Contents

1. [About the Project](#1-about-the-project)
2. [Tech Stack](#2-tech-stack)
3. [Architecture](#3-high-level-architecture-backend-only)
4. [Repository Layout](#4-repository-layout)
5. [Setup & Local Development](#5-setup--local-development)
6. [Environment Variables](#6-environment-variables)
7. [Running the API](#7-running-the-api)
8. [Database Schema](#8-database-schema)
9. [API Reference](#9-api-reference)
10. [Authentication Flow](#10-authentication-flow)
11. [Deployment to Google Cloud Run](#11-deployment-to-google-cloud-run)

---

## 1. About the Project

**Elara AI** is a service me and [@gaiborjouse](https://github.com/gaiborjosue) built for the **AI in Action 2025 Hackathon**. A user submits a medical concern (e.g. "I have a headache") and receives:

- the highest-rated medicinal plant (from our MongoDB Atlas dataset)
- a Gemini-generated recipe using that plant
- an optional PDF download of the recipe

All code lives in **backend/**.

✨ _This is my **first-ever** FastAPI project_ ✨, so every pattern and decision in here reflects a newcomer's learning journey.

**Data Source:** Our medicinal plant database is sourced from [Plants For A Future (PFAF)](https://pfaf.org/user/), a comprehensive online database of useful plants and their properties.

---

## 2. Tech Stack

| Layer / Concern  | Technology                                      |
| ---------------- | ----------------------------------------------- |
| Language         | Python 3.11                                     |
| Web Framework    | FastAPI + Uvicorn                               |
| Data Store       | MongoDB Atlas (shared M10)                      |
| Hosting          | Google Cloud Run (Docker container)             |
| LLM Services     | Vertex AI — Gemini Pro / Flash / Lite           |
| Auth             | OAuth2 Password Flow · JWT · Bcrypt             |
| Email Service    | SMTP (Gmail/SendGrid)                           |
| PDF Rendering    | WeasyPrint + Jinja2 template                    |
| Container Reg.   | Artifact Registry                               |
| Secrets          | Google Secret Manager (+ .env for local dev)    |
| CI / CD (opt-in) | Cloud Run                      |

---

## 3. Architecture (Backend Only)
![elaraBackendDiagram](https://github.com/user-attachments/assets/ba4451cf-fff8-4056-ab57-0ad19c4d1dab)

---

**What calls what?**
- `/getRecommendations` → `extract()` → `classifyCondition()` → `bestPlant()` → MongoDB
- `/getRecipe` → `getRecipe()` → Vertex AI
- `/downloadRecipePDF` → WeasyPrint
- Auth utilities touch the `users` collection.
- Email verification uses SMTP for sending verification emails.

---

## 4. Repository Layout

```
backend/
├─ app.py                      # FastAPI entry-point & routers
├─ Dockerfile
├─ requirements.txt
├─ auth/                       # 🔐 authentication helpers
│  ├─ hashing.py               #   bcrypt hashing
│  ├─ jwttoken.py              #   JWT creation / verification
│  └─ oauth.py                 #   OAuth2PasswordBearer dependency
├─ utils/
│  ├─ symptoms.py              # Gemini Lite symptom extractor
│  ├─ classification.py        # Gemini Flash condition classifier
│  ├─ recommender.py           # Mongo aggregation + hazard filter
│  └─ recipe.py                # Gemini Flash recipe generator
├─ templates/
│  └─ recipe.html              # Jinja2 → PDF template
├─ static/                     
└─ database/
    ├─ ingest.py               # **database seed script**
    └─ data/                   # raw CSV / JSON plant datasets
        ├─ pfaf_plants_merged.csv
        └─ pfaf_plants_merged_2.csv    
```

---

## 5. Setup & Local Development

The repo works perfectly fine **without** a dedicated virtual environment; just ensure you're on Python 3.11+ and install requirements:

```bash
cd backend
pip install -r requirements.txt

# Copy & fill secrets
cp .env.example .env
#   └─ set: MONGODB_URI, DB_NAME, COLL_NAME,
#          GOOGLE_PROJECT_ID, SERVICE_ACCOUNT_JSON,
#          SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES,
#          SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
#          FRONTEND_URL

# Seed the database (optional in dev)
python database/ingest.py

# Launch the API
uvicorn app:app --reload
```

Swagger UI lives at **http://localhost:8000/docs**.

---

## 6. Environment Variables

| Variable                       | Purpose                           |
| ------------------------------ | --------------------------------- |
| `MONGODB_URI`                  | Atlas SRV connection string       |
| `DB_NAME`, `COLL_NAME`         | database & collection names       |
| `GOOGLE_PROJECT_ID`            | Vertex AI project id              |
| `SERVICE_ACCOUNT_JSON`         | path/JSON creds for IAM           |
| `SECRET_KEY`                   | JWT signing key                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | token TTL                         |
| `SMTP_SERVER`                  | SMTP server for email sending    |
| `SMTP_PORT`                    | SMTP port (usually 587)          |
| `SMTP_USERNAME`                | SMTP username/email               |
| `SMTP_PASSWORD`                | SMTP password/app password        |
| `FRONTEND_URL`                 | Frontend URL for verification links |
| `PORT`                         | gunicorn/uvicorn port (Cloud Run) |

---

## 7. Running the API

**Local** (see [Setup & Local Development](#5-setup--local-development)) or **Docker**:

```bash
docker build -t elara-api backend
docker run --env-file backend/.env -p 8000:8080 elara-api
```

---

## 8. Database Schema

- **plants**
  - `latin_name_search`, `common_name_search`, `medicinal_rating_search`
  - `edibility_rating_search`, `Edible Uses`, `Known Hazards`, `plant_url`
- **users** (verified users only)
  - `email`, `username`, `hashed_password`, `email_verified`, `created_at`, `verified_at`
- **pending_users** (TTL = 24 hours)
  - `email`, `username`, `hashed_password`, `verification_token`, `verification_token_expires`, `created_at`
- **saved_recipes** (TTL = 10 days)
  - `recipe`, `deletedAt`, `user_id`

---

## 9. API Reference

| Verb   | Endpoint                   | Auth | Purpose                                   |
| ------ | -------------------------- | ---- | ----------------------------------------- |
| POST   | `/register`                | –    | create user with email verification       |
| POST   | `/verify-email`            | –    | verify email with token                   |
| POST   | `/resend-verification`     | –    | resend verification email                 |
| POST   | `/login`                   | –    | issue JWT (requires verified email)       |
| GET    | `/me`                      | ✅   | return current user                       |
| POST   | `/getRecommendations`      | ✅   | LLM adapters → best plant                 |
| POST   | `/getRecipe`               | ✅   | generate recipe via Gemini                |
| POST   | `/downloadRecipePDF`       | ✅   | render recipe → PDF                       |
| POST   | `/saveRecipe`              | ✅   | persist recipe                            |
| DELETE | `/deleteRecipe/{id}`       | ✅   | soft delete (sets `deletedAt`)            |
| GET    | `/recentlyDeletedRecipes`  | ✅   | list TTL-pending deletions                |

---

## 10. Authentication Flow

1. `/register` → `hashing.py` bcrypt → insert in `pending_users` → send verification email.
2. `/verify-email` → validate token → move user from `pending_users` to `users` → mark as verified.
3. `/login` → check user exists in `users` collection → return `access_token` via `jwttoken.py`.
4. Protected routes use `oauth.py` (`OAuth2PasswordBearer`).
5. Token verified → `jwttoken.verifyToken()`.

---

## 11. Deployment to Google Cloud Run

```bash
gcloud run deploy elarabackend --source . --region us-central1 --service-account ${SERVICE_ACCOUNT_EMAIL} --allow-unauthenticated --project ${GCP_PROJECT_ID} --set-secrets="MONGODB_URI=mongodb-uri:latest,DB_NAME=db-name:latest,COLL_NAME=coll-name:latest,SECRET_KEY=jwt-secret-key:latest,ALGORITHM=jwt-algorithm:latest,EXPIRE_MINUTES=jwt-expire-minutes:latest,PROJECT=project:latest,SMTP_SERVER=smtp-server:latest,SMTP_PORT=smtp-port:latest,SMTP_USERNAME=smtp-username:latest,SMTP_PASSWORD=smtp-password:latest,FRONTEND_URL=frontend-url:latest"
```

Cloud Run autoscales 0 → N (cold starts ≈1 s).

