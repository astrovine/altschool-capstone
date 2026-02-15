from pydantic import BaseModel
from typing import Any, Optional


class Msg(BaseModel):
    detail: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PageParams(BaseModel):
    page: int = 1
    size: int = 20

    def offset(self) -> int:
        return (self.page - 1) * self.size
