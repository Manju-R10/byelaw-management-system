"""Service layer — business logic orchestrating repositories, security and validation.

Routers stay thin: they parse/validate input, call a service, and shape the response.
All domain rules live here.
"""
