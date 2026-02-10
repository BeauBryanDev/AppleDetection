# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Apple Yield Estimator** is a computer vision system for detecting and counting apples in orchard images. The system uses YOLOv8s (ONNX format) for real-time apple detection with health classification.

- **Backend**: FastAPI-based REST API (Python 3.11+)
- **Frontend**: React + Vite (JavaScript)
- **Database**: PostgreSQL 15
- **ML Model**: YOLOv8s ONNX (detects "apple", "damaged_apple" classes)
- **Deployment**: Docker Compose

## Development Commands

### Backend (FastAPI)

```bash
# Local development (requires PostgreSQL running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with Python module
python -m uvicorn app.main:app --reload

# Direct execution
python -m app.main

# Database only (for local dev)
docker compose up db -d

# Full stack with Docker
docker compose up --build -d

# View logs
docker compose logs -f backend

# Stop services
docker compose down
```

### Frontend (React + Vite)

```bash
cd frontend

# Development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/api/test_estimator.py

# Manual API testing script
python test_api.py
```

### Database Management

```bash
# Access PostgreSQL container
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>

# Seed database with test data
python seed_db.py

# Check database connection
python -c "from app.db.session import engine; print(engine.url)"
```

## Architecture Overview

### Backend Structure

**Core Application Layer:**
- `app/main.py` - FastAPI application entry point, CORS configuration, router registration
- `app/core/config.py` - Centralized settings management using Pydantic BaseSettings (reads from .env)
- `app/core/security.py` - JWT token handling, password hashing (bcrypt)
- `app/api/deps.py` - FastAPI dependency injection for authentication, authorization, pagination

**API Layer (Versioned):**
- `app/api/v1/endpoints/` - API endpoints organized by domain:
  - `estimator.py` - Main inference endpoint for apple detection
  - `auth.py` - Login, registration, token management
  - `users.py` - User CRUD operations (admin-only)
  - `farming.py` - Orchard and tree management
  - `history.py` - Historical yield records
  - `analytics.py` - Statistics and aggregations

**Database Layer:**
- `app/db/session.py` - SQLAlchemy engine, session factory
- `app/db/base.py` - Base class for all models
- `app/db/models/` - SQLAlchemy ORM models:
  - `users.py` - User authentication (role-based: ADMIN, FARMER, GUEST)
  - `farming.py` - Domain models: Orchard, Tree, Image, Prediction, Detection, YieldRecord

**ML Inference Layer:**
- `app/models/inference.py` - YOLOv8 inference engine:
  - **AppleInference class**: Loads ONNX model, handles preprocessing/postprocessing
  - **Preprocessing**: Resize to 640x640, BGR→RGB, normalize [0,1], CHW format
  - **Detection**: ONNX Runtime (CPU), confidence=0.45, NMS=0.45
  - **Output**: Counts (healthy, damaged, total), bounding boxes, class IDs, confidences
- `app/models/weights/best_model.onnx` - Trained YOLOv8s model (640x640 input)
- `app/utils/image_processing.py` - Post-detection visualization (draws bounding boxes)

**Schemas:**
- `app/schemas/yield_schema.py` - Pydantic models for request/response validation

### Authentication Flow

The API uses **JWT Bearer token authentication** with role-based access control:

1. User logs in via `POST /api/v1/auth/login` → receives JWT access token
2. Token is passed in `Authorization: Bearer <token>` header
3. `app/api/deps.py` provides dependency injectors:
   - `get_current_user()` - Requires valid token (401 if missing/invalid)
   - `get_current_user_optional()` - Returns None if no token (guest mode)
   - `get_current_active_user()` - Requires active user (403 if inactive)
   - `get_current_active_admin()` - Requires ADMIN role (403 otherwise)

**Guest vs Authenticated Usage:**
- Endpoints can support **guest mode** (unauthenticated) by accepting `orchard_id=None`
- Authenticated users can associate predictions with specific orchards/trees they own
- Admins can access all resources regardless of ownership

### Frontend Structure

- `frontend/src/main.jsx` - App entry point, React Router setup
- `frontend/src/App.jsx` - Root component with route definitions
- `frontend/src/context/AuthContext.jsx` - Global authentication state management
- `frontend/src/layouts/` - Layout wrappers (AuthLayout, DashboardLayout)
- `frontend/src/pages/` - Page components (Login, Dashboard, Estimator)
- `frontend/src/components/` - Reusable UI components
- `frontend/src/api/` - API client functions (axios)

### Key Design Patterns

**Database Models Inheritance:**
- All models extend `app.db.base.Base` (SQLAlchemy declarative base)
- Models are registered in `app/db/models/__init__.py` for auto-discovery
- Tables are auto-created on startup via `Base.metadata.create_all(bind=engine)`

**Dependency Injection:**
- FastAPI dependencies handle cross-cutting concerns (auth, validation, DB sessions)
- `get_db()` provides scoped database sessions with automatic cleanup
- Security dependencies compose: `get_current_user` → `get_current_active_user` → `get_current_active_admin`

**Image Upload Flow:**
1. Client uploads image → `POST /api/v1/estimator/estimate`
2. Validate file type and size
3. Save to `uploads/` directory with UUID filename
4. Run inference via `model_engine.run_inference()`
5. Create database records: Image → Prediction → Detections
6. Return JSON response with counts and detection metadata
7. Optionally draw bounding boxes and save annotated image

**Configuration Management:**
- All settings in `app/core/config.py` use Pydantic validation
- Priority: Environment variables > .env file > default values
- Settings loaded once at startup via `settings = Settings()`
- Access via `from app.core.config import settings`

## Important Notes

### Model Inference Details

- **Model path**: `app/models/weights/best_model.onnx`
- **Input shape**: (1, 3, 640, 640) - NCHW format
- **Classes**: `["apple", "damaged_apple"]` (indexes 0, 1)
- **Confidence threshold**: 0.45 (configurable in `app/core/config.py`)
- **NMS threshold**: 0.45 (to remove duplicate detections)
- The model is loaded once at module import (`model_engine = AppleInference(model_path)`)
- Color-based classification logic exists but is currently disabled (see `_classify_apple_color` in inference.py)

### Environment Variables

**Critical variables (must be set in .env):**
- `SECRET_KEY` - JWT signing key (min 32 chars, generate with `openssl rand -hex 32`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials

**Optional but recommended:**
- `DEBUG=True` - Enable debug mode (disable in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES=30` - JWT expiration time
- `CONFIDENCE_THRESHOLD=0.45` - Model detection threshold
- `BACKEND_CORS_ORIGINS` - Comma-separated allowed origins

### Docker Deployment

The `docker-compose.yml` orchestrates two services:
- **db**: PostgreSQL 15 (port 5432, persists data in `postgres_data` volume)
- **backend**: FastAPI app (port 8000, waits for DB health check)

**Important**: The backend container expects the model file to exist at build time. Ensure `app/models/weights/best_model.onnx` is present before running `docker compose build`.

### Database Schema

Core tables:
- `users` - Authentication and authorization
- `orchards` - User-owned orchards (name, location, area)
- `trees` - Individual trees within orchards (tree_number, variety)
- `images` - Uploaded images (filename, dimensions, upload timestamp)
- `predictions` - Inference results (healthy_count, damaged_count, health_index)
- `detections` - Individual bounding box detections (bbox coordinates, class_id, confidence)
- `yield_records` - Legacy table for backward compatibility

### Frontend API Integration

The frontend expects the backend at `http://localhost:8000` by default. Configure CORS in `app/main.py` to allow frontend origin (already includes `http://localhost:5173` for Vite dev server).

API calls use axios configured in `frontend/src/api/`. Authentication token is stored in localStorage and added to request headers automatically.

**Frontend Pages:**
- `/dashboard` - Main dashboard with orchard overview and recent activity
- `/estimator` - Image upload and apple detection interface
- `/farming` - CRUD interface for orchards and trees management
- `/analytics` - Analytics dashboard with charts and statistics
- `/history` - Historical yield records with search and pagination
- `/users` - User management (admin only)

**API Services (frontend/src/api/):**
- `axios.js` - Axios client with auth interceptor
- `auth.js` - Login, register, verify token
- `farming.js` - Orchards, trees, and images CRUD
- `analytics.js` - Dashboard metrics, trends, summaries
- `history.js` - Yield records history
- `users.js` - User management endpoints
- `estimator.js` - Image upload for detection

**UI Components (Cyberpunk Theme):**
- Colors: `cyber-black` (#050505), `apple-green` (#39ff14), `apple-red` (#ff073a)
- Components: Button, Card, Input, Label with neon glow effects
- Layout: Fixed sidebar with role-based menu items
- Authentication: Protected routes using AuthContext

### Common Pitfalls

1. **ONNX model not found**: Ensure `app/models/weights/best_model.onnx` exists. The app will fail to start if missing.
2. **Database connection failed**: Verify PostgreSQL is running and credentials in `.env` match `docker-compose.yml`.
3. **CORS errors**: Add frontend origin to `BACKEND_CORS_ORIGINS` in `.env` or `origins` list in `app/main.py`.
4. **JWT authentication errors**: Ensure `SECRET_KEY` is set in `.env` and token is passed in `Authorization: Bearer <token>` header.
5. **File upload limits**: Max 10MB by default (see `MAX_FILE_SIZE_MB` in config.py).

### Git Workflow

Recent commit pattern shows:
- Feature branches for new functionality
- Refactoring commits for code improvements
- Security/auth-focused commits for endpoint protection

When making changes:
- Keep model inference logic in `app/models/inference.py`
- Database schema changes require updating `app/db/models/`
- API changes should be versioned under `app/api/v1/endpoints/`
- Frontend changes go in `frontend/src/`
