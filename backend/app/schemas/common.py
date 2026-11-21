from typing import Annotated, Any, Generic, Literal, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field


ResourceId = Annotated[int, Field(gt=0, le=2**63 - 1)]
Term = Annotated[str, Field(min_length=1, max_length=20)]
T = TypeVar("T")


class Items(BaseModel, Generic[T]):
    items: list[T]
    total: int


class Page(Items[T], Generic[T]):
    page: int
    size: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class FieldIssue(BaseModel):
    field: str
    message: str


class ValidationErrorDetails(BaseModel):
    fields: list[FieldIssue]


class ValidationErrorBody(BaseModel):
    code: Literal["VALIDATION_ERROR"]
    message: str
    details: ValidationErrorDetails


class ValidationErrorResponse(BaseModel):
    error: ValidationErrorBody


class PageParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, le=2**63 - 1)] = 1,
        size: Annotated[int, Query(ge=1, le=100)] = 20,
    ):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return min((self.page - 1) * self.size, 2**63 - 1)


Pagination = Annotated[PageParams, Depends()]
