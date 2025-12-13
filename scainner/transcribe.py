import threading
import time
from datetime import datetime, timedelta, timezone
from multiprocessing import Event

from core.notifications import SlackNotificationsClient
from core.scainner import Scainner
from db.mongo import (
    clear_audio_older_than_30_days,
    close_client,
    get_transcriptions_collection,
)
from settings import application_settings

NOTIFICATIONS_CLIENT = None
if application_settings.slack_webhook_url:
    NOTIFICATIONS_CLIENT = SlackNotificationsClient(
        application_settings.slack_webhook_url,
        application_settings.notification_patterns_list,
    )


def audio_cleanup():
    print("Audio cleanup thread started")
    while True:
        print("Cleaning up audio files over 30 days old...")
        clear_audio_older_than_30_days()
        time.sleep(24 * 60 * 60)  # Run every 24 hours


def start_audio_cleanup_thread():
    cleanup_thread = threading.Thread(target=audio_cleanup, daemon=True)
    cleanup_thread.start()
    return cleanup_thread


def start(shutdown_event: Event):
    """
    Start the transcription loop.

    Args:
        shutdown_event: Event to signal when shutdown is requested.
                       The loop checks this event and exits gracefully when set.
    """
    transcriber = Scainner(
        application_settings.endpoint,
        application_settings.whisper_model_size,
        application_settings.whisper_compute_type,
    )
    last_fetch_time = datetime.now(tz=timezone.utc) - timedelta(
        seconds=application_settings.fetch_interval
    )
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
                        transcriptions_collection.insert_one(call.model_dump())
                    except Exception as e:
                        print(f"ERROR: Failed to insert call into db {e}")
                if NOTIFICATIONS_CLIENT:
                    NOTIFICATIONS_CLIENT.notify_if_matches(call.transcription)
                last_fetch_time = call.timestamp

            # Interruptible sleep. Exits immediately if shutdown_event is set.
            if shutdown_event.wait(timeout=application_settings.fetch_interval):
                break
    finally:
        close_client()
        print("Stopping transcription")
