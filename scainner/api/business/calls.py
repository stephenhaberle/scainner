import asyncio
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from db.mongo import get_transcriptions_collection
from models.call import CallFilterParams, CallResponse
from pymongo import ASCENDING
from settings import application_settings

call_collection = get_transcriptions_collection()


def get_all_calls(filter_params: CallFilterParams) -> list[CallResponse] | None:
    """
    Get all calls from the database.

    Args:
        filter_params: The filter parameters for the calls.

    Returns:
        A list of CallResponse objects or None if none are found.
    """
    if call_collection is None:
        print("WARNING: Request for calls was received but MongoDB is not configured")
        return None
    return [
        CallResponse(**call)
        for call in call_collection.find()
        .skip(filter_params.offset)
        .limit(filter_params.limit)
        .sort(filter_params.order_by, filter_params.get_order_direction())
    ]


def get_call_by_id(call_id: str) -> CallResponse | None:
    """
    Get a call from the database by its ID.

    Args:
        call_id: The ID of the call.

    Returns:
        A CallResponse object or None if the call is not found.
    """
    if call_collection is None:
        print(
            "WARNING: Request for call by ID was received but MongoDB is not configured"
        )
        return None
    try:
        call = call_collection.find_one({"_id": ObjectId(call_id)})
    except InvalidId:
        call = None
        print(f"ERROR: Call ID {call_id} is not a valid ObjectId")
    if call is None:
        return None
    return CallResponse(**call)


async def stream_calls(after_datetime: datetime):
    """
    Stream calls from the database.

    Args:
        after_datetime: The timestamp to start streaming calls after.

    Yields:
        A generator of CallResponse objects.
    """
    try:
        print(f"INFO: Streaming calls after {after_datetime}")
        if call_collection is None:
            print("WARNING: Stream request received but MongoDB is not configured")
            return

        while True:
            calls = call_collection.find({"timestamp": {"$gt": after_datetime}}).sort(
                "timestamp", ASCENDING
            )
            for call in calls:
                yield f"data: {CallResponse(**call).model_dump_json()}\n\n"
                after_datetime = call["timestamp"]
            await asyncio.sleep(application_settings.stream_db_poll_interval)
    finally:
        print("INFO: Stream closed")
