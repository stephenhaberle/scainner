from db.mongo import get_transcriptions_collection
from fastapi import APIRouter, HTTPException
from models.call import CallResponse

router = APIRouter()

call_collection = get_transcriptions_collection()


@router.get("/calls")
def get_all_calls() -> list[CallResponse]:
    if call_collection is None:
        raise HTTPException(status_code=500, detail="MongoDB is not configured")
    return [CallResponse(**call) for call in call_collection.find()]


@router.get("/calls/{call_id}")
def get_call_by_id(call_id: str):
    if call_collection is None:
        raise HTTPException(status_code=500, detail="MongoDB is not configured")
    return CallResponse(**call_collection.find_one({"_id": call_id}))
