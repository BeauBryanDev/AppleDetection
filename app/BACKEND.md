# 🍎 Apple Yield Estimator API — Backend Architecture

A modular, production‑ready **FastAPI** backend for an apple yield estimation system.  
It serves a fine‑tuned **YOLOv8s** model (exported to **ONNX**) to detect and count apples from orchard images, while managing users, farming records, and historical data via **PostgreSQL**.

---

## 📐 Overall Architecture – Quick Overview

The backend follows **clean architecture** principles: separation of concerns, dependency injection, and API versioning. It is fully containerized with Docker.

| Layer        | Technology                         |
|--------------|------------------------------------|
| **API**      | FastAPI (async, automatic OpenAPI) |
| **Database** | PostgreSQL + SQLAlchemy ORM        |
| **Model**    | YOLOv8s → ONNX Runtime             |
| **Validation**| Pydantic v2                       |
| **Auth**     | JWT (bcrypt + PyJWT)              |
| **Container**| Docker (backend + DB)             |

**Entry point**: `main.py` – creates the FastAPI app, includes routers, sets up CORS, and runs with Uvicorn.

---

## 📁 Folder‑by‑Folder Breakdown

### `api/` – The Front Door for Clients
All HTTP routes, dependencies, and versioning live here.

```
├── app
│   ├── api
│   │   ├── deps.py
│   │   ├── __init__.py
│   │   └── v1
│   │       ├── api.py
│   │       └── endpoints
│   │           ├── analytics.py
│   │           ├── auth.py
│   │           ├── estimator.py
│   │           ├── farming.py
│   │           ├── helper.py
│   │           ├── history.py
│   │           └── users.py
│   ├── core
│   │   ├── config.py
│   │   ├── exception.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db
│   │   ├── base.py
│   │   ├── deprecated_models.py
│   │   ├── migrations
│   │   │   └── migrations.py
│   │   ├── models
│   │   │   ├── farming.py
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   └── session.py
│   ├── __init__.py
│   ├── main.py
│   ├── models
│   │   ├── helper.py
│   │   ├── inference.py
│   │   ├── __init__.py
│   │   ├── predictor.py
│   │   └── weights
│   │       ├── apples.py
│   │       ├── best_model.onnx
│   │       ├── mango.py
│   │       ├── model_metadata.json
│   │       ├── orange.py
│   │       └── peach.py
│   ├── schemas
│   │   ├── image_schema.py
│   │   ├── orchard_schema.py
│   │   ├── tree_schema.py
│   │   ├── user_schema.py
│   │   └── yield_schema.py
│   └── utils
│       ├── helper.py
│       ├── helpers.py
│       ├── image_processing.py
│       └── validators.py
├── docker-compose.yml
├── Dockerfile
├── helper.py
├── LICENSE
├── notes.txt
├── README.md
├── requirements.txt
├── scrpts
│   ├── export_model.py
│   ├── init_db.py
│   └── seed_data.py
├── seed_db.py
├── test_api.py
├── test_apple_img.jpg
├── tests
│   ├── api
│   │   ├── __init__.py
│   │   └── test_estimator.py
│   ├── conftest.py
│   ├── __init__.py
│   ├── users
│   │   └── test_users_crud.py
│   └── utils
│       └── test_img_processing.py
├── tree.txt
└── uploads
```

🔹 **Why this works**  
- **`deps.py`** keeps code DRY – e.g., `get_db()` yields a SQLAlchemy session, `get_current_user()` verifies JWT.  
- **Versioning** (`v1/`) ensures backward compatibility when you extend the API.  
- **Separated endpoints** – each domain (auth, farming, estimation) is isolated, making new features easy to add.

---

### `core/` – Shared Foundations
Configuration, security, logging, and custom exceptions.

```
core/
├── config.py # Loads .env variables (DB_URL, SECRET_KEY, ALGORITHM)
├── security.py # Password hashing (bcrypt), JWT create/decode
├── exception.py # Custom exceptions → HTTP error responses
└── logging.py # Structured logging setup (debug inference issues)
```

🔹 **Why this works**  
- Environment‑based config – **no hardcoded secrets**.  
- Centralised **security** – easy to audit and update auth logic.  
- Custom **exceptions** (e.g., `ModelInferenceError`) map to clean HTTP status codes.

---

### `db/` – PostgreSQL & SQLAlchemy
ORM layer for persistent storage.

```
db/
├── base.py # Base class for all models
├── deprecated_models.py # Models to be removed in future versions
├── migrations # Database migrations
│   └── migrations.py
├── models # Models for ORM
│   ├── farming.py
│   ├── __init__.py
│   └── users.py
└── session.py # SQLAlchemy session
```

🔹 **Why this works**  
- ORM – easy to query, update, and delete data.
- **SQLAlchemy ORM** maps Python classes to PostgreSQL tables.  
- **Migrations** let you evolve the schema without losing data.  
- Clear separation between **active** and **deprecated** models.

---

### `models/` – Machine Learning (Not to be confused with DB models)
Your trained YOLOv8s model, exported to ONNX for lightweight inference.

```
models/
├── weights/
│ ├── best_model.onnx # Fine‑tuned YOLOv8s (gitignored)
│ ├── best_model2.onnx # Experiment variant
│ └── model_metadata.json # Input shape, classes, metrics
├── inference.py # ONNX Runtime session, pre/post‑processing
├── predictor.py # Predictor class (load model, predict(image))
├── apples.py # Apple‑specific loader / metadata
└── (mango.py, orange.py …) # Extensible – placeholders for other fruits
```

🔹 **Why this works**  
- **ONNX** = cross‑platform, faster inference than raw PyTorch, smaller footprint.  
- **Predictor class** encapsulates model logic – swap YOLO versions without touching routes.  
- **Extensible by design** – add `mango.py`, `peach.py` tomorrow.

---

### `schemas/` – Pydantic Validation
Define **how data enters and leaves** the API.

```schemas/
├── user_schema.py # UserCreate, UserOut (password hidden)
├── image_schema.py # ImageUpload (file, metadata)
├── orchard_schema.py # OrchardBase, OrchardCreate
├── tree_schema.py # Tree schemas
└── yield_schema.py # YieldResponse (red/damaged/green counts)

```

🔹 **Why this works**  
- Automatic request **validation** and **serialization**.  
- Prevents malformed data from ever reaching the model or DB.  
- OpenAPI docs auto‑generated from these schemas.

---

### `utils/` – Reusable Helpers
Shared logic that doesn’t belong to a single feature.

```utils/
├── image_processing.py # Preprocess (resize, normalize) + postprocess (count classes)
├── helpers.py # Date formatting, string utils
└── validators.py # Custom email, image‑format validators
```

🔹 **Why this works**  
- **`image_processing.py`** is critical – feeds clean, correctly sized tensors to the ONNX model.  
- Keeps endpoint code **lean** and focused on business logic.

---

## 🔐 Security & Auth Flow

1. User logs in → `POST /v1/auth/login`  
2. Password verified (bcrypt) → JWT access token issued.  
3. Token sent in `Authorization: Bearer <token>` header.  
4. `deps.get_current_user()` validates token and injects `User` into endpoint.  

*Stateless, scalable, ready for mobile/web clients.*

---

## 🐳 Deployment with Docker

The project is fully containerised:

- **Backend container**: FastAPI + Uvicorn + ONNX Runtime  
- **Database container**: PostgreSQL 15  

Docker Compose orchestrates both, with volumes for persistent DB storage and `.env` for secrets.

---

## 🧪 Testing & Maintainability

- **Dependency injection** makes unit testing easy (mock DB, mock model inference).  
- **Separated concerns** → you can update the estimator logic without touching auth.  
- **API versioning** → future v2 can coexist with v1.  

---

## 🗺️ Project Roadmap – Built to Grow

| Step | Feature                          | Status |
|------|----------------------------------|--------|
| 1    | YOLOv8s fine‑tuned on Roboflow  | ✅ Done |
| 2    | ONNX export + inference wrapper | ✅ Done |
| 3    | FastAPI with JWT auth           | ✅ Done |
| 4    | PostgreSQL + SQLAlchemy        | ✅ Done |
| 5    | Batch image processing         | ✅ Done |
| 6    | **Add citrus / stone fruit models** | 🔜 Next |
| 7    | Frontend (React) integration   | 🚀 Planned |

---

## 🏁 Quick Start (Dev)

```bash
# 1. Clone & enter
git clone https://github.com/yourname/apple-yield-estimator-api
cd apple-yield-estimator-api

# 2. Environment
cp .env.example .env   # edit DB_URL, SECRET_KEY

# 3. Docker
docker-compose up --build

# 4. API docs
open http://localhost:8000/docs

```
