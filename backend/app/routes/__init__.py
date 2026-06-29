"""API route handlers"""
from app.routes import auth, users, projects, dashboard, asset_types, resources
from app.routes import templates, assets, resource_types

__all__ = [
    "auth",
    "users",
    "projects",
    "dashboard",
    "asset_types",
    "resources",
    "templates",
    "assets",
    "resource_types",
]