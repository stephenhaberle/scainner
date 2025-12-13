import os
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from multiprocessing import Event

from core.audio_cleanup import start_audio_cleanup_thread
from core.notifications import SlackNotificationsClient
from core.scainner import Scainner
from db.mongo import close_client, get_transcriptions_collection
from dotenv import load_dotenv

load_dotenv()
ENDPOINT = os.getenv("ENDPOINT")
if not ENDPOINT:
    print("ERROR: ENDPOINT is not set")
    exit(1)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
FETCH_INTERVAL = os.getenv("FETCH_INTERVAL")
FETCH_INTERVAL = int(FETCH_INTERVAL) if FETCH_INTERVAL else 900
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE")
WHISPER_MODEL_SIZE = WHISPER_MODEL_SIZE if WHISPER_MODEL_SIZE else "distil-small.en"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE")
WHISPER_COMPUTE_TYPE = WHISPER_COMPUTE_TYPE if WHISPER_COMPUTE_TYPE else "default"

NOTIFICATION_PATTERNS = os.getenv("NOTIFICATION_PATTERNS")
if NOTIFICATION_PATTERNS:
    # Split by &&& and strip whitespace from each pattern
    patterns = [
        pattern.strip()
        for pattern in NOTIFICATION_PATTERNS.split("&&&")
        if pattern.strip()
    ]
    NOTIFICATION_PATTERNS = patterns if patterns else None

NOTIFICATIONS_CLIENT = None
if SLACK_WEBHOOK_URL:
    NOTIFICATIONS_CLIENT = SlackNotificationsClient(
        SLACK_WEBHOOK_URL, NOTIFICATION_PATTERNS
    )


def start(shutdown_event: Event):
    """
    Start the transcription loop.

    Args:
        shutdown_event: Event to signal when shutdown is requested.
                       The loop checks this event and exits gracefully when set.
    """
    transcriber = Scainner(ENDPOINT, WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE)
    last_fetch_time = datetime.now(tz=timezone.utc) - timedelta(seconds=FETCH_INTERVAL)
    transcriptions_collection = get_transcriptions_collection()
    if transcriptions_collection is not None:
        start_audio_cleanup_thread()
    else:
        print("MongoDB not configured. Database calls will be skipped")
    try:
        print("Starting transcription")
        while not shutdown_event.is_set():
            print(f"Looking for new calls after {last_fetch_time}...")
            for call in transcriber.transcribe_calls(min_call_time=last_fetch_time):
                print(
                    f"{call.timestamp}: {call.transcription} ({call.transcription_time:.2f}s)"
                )
                if transcriptions_collection is not None:
                    try:
                        transcriptions_collection.insert_one(asdict(call))
                    except Exception as e:
                        print(f"ERROR: Failed to insert call into db {e}")
                if NOTIFICATIONS_CLIENT:
                    NOTIFICATIONS_CLIENT.notify_if_matches(call.transcription)
                last_fetch_time = call.timestamp

            # Interruptible sleep. Exits immediately if shutdown_event is set.
            if shutdown_event.wait(timeout=FETCH_INTERVAL):
                break
    finally:
        close_client()
        print("Stopping transcription")
