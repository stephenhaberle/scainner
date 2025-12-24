from datetime import datetime, timezone
from typing import Annotated

from api.business.calls import get_all_calls, get_call_by_id, stream_calls
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from models.call import CallFilterParams, CallResponse

router = APIRouter()


@router.get("/calls")
def get_all_calls_route(
    filter_params: Annotated[CallFilterParams, Query()],
) -> list[CallResponse]:
    calls = get_all_calls(filter_params)
    if calls is None:
        raise HTTPException(status_code=404, detail="Calls not found")
    return calls


@router.get("/calls/stream")
async def stream_calls_route() -> StreamingResponse:
    timestamp = datetime.now(tz=timezone.utc)
    return StreamingResponse(stream_calls(timestamp), media_type="text/event-stream")


@router.get("/calls/{call_id}")
def get_call_by_id_route(call_id: str) -> CallResponse | None:
    call = get_call_by_id(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
