from fastapi import APIRouter
from app.api.v1.endpoints import estimator, history, analytics, users, farming
from app.api.v1.endpoints import auth

api_router = APIRouter()


api_router.include_router(estimator.router, prefix="/estimator", tags=["Estimator"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(farming.router, prefix="/farming", tags=["Farming"])