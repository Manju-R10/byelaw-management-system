"""Aggregates all v1 routers into a single router mounted by the application."""
from fastapi import APIRouter

from app.api.v1 import auth, byelaws, clauses, roles, search, users, workflow

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(roles.permissions_router)
api_router.include_router(byelaws.router)
api_router.include_router(clauses.byelaw_clauses_router)
api_router.include_router(clauses.clauses_router)
api_router.include_router(search.router)
api_router.include_router(workflow.router)
api_router.include_router(workflow.notifications_router)

# Subsequent modules (export, audit ...) register here as they are implemented,
# keeping main.py free of per-module wiring.
