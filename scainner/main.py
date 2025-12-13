from contextlib import asynccontextmanager
from multiprocessing import Event, Process

import uvicorn
from api.app import create_app

transcription_process: Process | None = None
shutdown_event = Event()


def run_transcription_worker(shutdown_event: Event):
    """
    Runs the transcription worker. Lazy imports the start method to avoid loading the whisper model until the process is started.
    Transcription worker is run in a separate process to avoid blocking the main process with its CPU heavy operations.

    Args:
        shutdown_event: Event to signal when shutdown is requested.
    """
    from transcribe import start

    try:
        start(shutdown_event)
    except Exception as e:
        print(f"ERROR: Transcription worker error: {e}")
    finally:
        from db.mongo import close_client

        close_client()


@asynccontextmanager
async def lifespan(app):
    """
    FastAPI lifespan context manager.
    Starts the transcription worker and yields the FastAPI app.
    Shuts down the transcription worker on shutdown.

    Args:
        app: FastAPI app instance.

    Yields:
        FastAPI app instance.
    """
    global transcription_process

    transcription_process = Process(
        target=run_transcription_worker, args=(shutdown_event,), daemon=False
    )
    transcription_process.start()
    print("Started transcription worker")

    yield

    print("Shutting down transcription worker...")
    shutdown_event.set()
    if transcription_process:
        transcription_process.join(timeout=10)
        if transcription_process.is_alive():
            print("Join timeout reached. Forcing termination...")
            transcription_process.terminate()
            transcription_process.join()


api = create_app(lifespan=lifespan)


def main():
    uvicorn.run(api, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
