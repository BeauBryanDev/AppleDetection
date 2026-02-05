from fastapi import APIRouter
from app.api.v1.endpoints import estimator, history, analytics, users

api_router = APIRouter()

# Aquí es donde ocurre la magia: organizas por etiquetas (tags)
api_router.include_router(estimator.router, prefix="/estimator", tags=["Estimator"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])