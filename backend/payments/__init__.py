"""Payments blueprint initialization."""
from flask import Blueprint

payments_bp = Blueprint("payments", __name__, url_prefix="/api")

from backend.payments import routes
