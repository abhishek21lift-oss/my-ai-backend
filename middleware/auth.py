"""
Auth middleware is intentionally thin — it just propagates the
X-API-Key header to downstream routes. Actual validation happens
in the `get_current_user` FastAPI dependency so Swagger UI,
/health, and other unprotected routes are left untouched.
"""
