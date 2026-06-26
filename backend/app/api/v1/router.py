"""Aggregates all v1 routers into a single router mounted by the application."""
from fastapi import APIRouter

from app.api.v1 import auth, byelaws, roles, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(roles.permissions_router)
api_router.include_router(byelaws.router)

# Subsequent modules (extraction, review, search, export, audit ...) register here as
# they are implemented, keeping main.py free of per-module wiring.
