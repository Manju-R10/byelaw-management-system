"""Repository layer — encapsulates all database access behind plain functions/classes.

Keeping queries here (rather than in services or routers) honours the Repository
pattern: services depend on these abstractions, not on SQLAlchemy query details.
"""
