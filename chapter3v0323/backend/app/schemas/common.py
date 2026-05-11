from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class APIBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimestampRead(ORMBaseModel):
    created_at: datetime
    updated_at: datetime
