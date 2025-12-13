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

    @app.get("/")
    def read_root():
        return {"message": "Hello, World!"}

    return app
