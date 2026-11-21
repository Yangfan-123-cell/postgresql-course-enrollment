from typing import Literal

from pydantic import BaseModel


StrategyName = Literal["V0", "V1", "V2", "V3"]


class StrategyState(BaseModel):
    strategy: StrategyName


class PingResponse(BaseModel):
    status: Literal["ok"] = "ok"
