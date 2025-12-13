from api.routes import calls
from fastapi import FastAPI


def create_app(lifespan=None):
    """
    Create and configure the FastAPI application.

    Args:
        lifespan: Optional lifespan context manager for startup/shutdown events.

    Returns:
        Configured FastAPI app instance.
    """
    app = FastAPI(lifespan=lifespan)

    app.include_router(calls.router)

    return app
