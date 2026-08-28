"""Aggregate API router. New phase routers are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import documents, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)

# Phase 2+ routers are added here as they land:
# api_router.include_router(query.router)
