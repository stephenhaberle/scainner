from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from db.mongo import get_transcriptions_collection
from fastapi import APIRouter, HTTPException, Query
from models.call import CallFilterParams, CallResponse

router = APIRouter()

call_collection = get_transcriptions_collection()


@router.get("/calls")
def get_all_calls(
    filter_params: Annotated[CallFilterParams, Query()],
) -> list[CallResponse]:
    if call_collection is None:
        raise HTTPException(status_code=500, detail="MongoDB is not configured")
    return [
        CallResponse(**call)
        for call in call_collection.find()
        .skip(filter_params.offset)
        .limit(filter_params.limit)
        .sort(filter_params.order_by, filter_params.get_order_direction())
    ]


@router.get("/calls/{call_id}")
def get_call_by_id(call_id: str) -> CallResponse:
    if call_collection is None:
        raise HTTPException(status_code=500, detail="MongoDB is not configured")

    try:
        call = call_collection.find_one({"_id": ObjectId(call_id)})
    except InvalidId:
        call = None
        print(f"ERROR: Call ID {call_id} is not a valid ObjectId")
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallResponse(**call)
