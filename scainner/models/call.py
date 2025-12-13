import base64
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
# https://www.mongodb.com/docs/languages/python/pymongo-driver/current/integrations/fastapi-integration/
PyObjectId = Annotated[str, BeforeValidator(str)]


class Call(BaseModel):
    """
    A call from the OpenMHz API.
    """

    src_id: str = Field(..., description="The source ID of the call in OpenMHz")
    url: str = Field(..., description="The URL of the call in OpenMHz")
    star_count: int = Field(
        ..., description="The number of stars the call has received"
    )
    length: int = Field(..., description="The length of the call in seconds")
    timestamp: datetime = Field(..., description="The timestamp of the call")
    frequency: int = Field(..., description="The frequency of the call")
    talkgroup_number: int = Field(..., description="The talkgroup number of the call")
    model_size: str = Field(
        ..., description="The model size used to transcribe the call"
    )
    transcription: str = Field(None, description="The transcription of the call")
    transcription_time: float = Field(
        None, description="The time taken to transcribe the call in seconds"
    )
    audio: bytes | None = Field(None, description="The audio of the call in bytes")


class CallResponse(Call, BaseModel):
    """
    A call response from the API.
    """

    db_id: PyObjectId = Field(
        ..., description="The database ID of the call in MongoDB", alias="_id"
    )

    def model_post_init(self, __context) -> None:
        if self.audio is not None and isinstance(self.audio, bytes):
            self.audio = base64.b64encode(self.audio).decode("utf-8")
