"""Pydantic request/response models — the HTTP contract for the API layer."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from domain_services.enums import OrderStatus, PaymentMethod, RequestStatus, Role


class LoginIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=1, max_length=32)
    price: Decimal = Field(ge=0)
    quantity: int = Field(default=0, ge=0)
    shelf_location: str = Field(default="", max_length=64)


class BookEdit(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    price: Decimal | None = Field(default=None, ge=0)
    shelf_location: str | None = Field(default=None, max_length=64)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    price: Decimal
    quantity: int
    shelf_location: str
    active: bool


class ReceiveIn(BaseModel):
    quantity: int = Field(gt=0)
    note: str = Field(default="", max_length=255)


class CorrectIn(BaseModel):
    quantity: int = Field(ge=0)
    note: str = Field(default="", max_length=255)


class CartLineIn(BaseModel):
    book_id: int
    quantity: int = Field(gt=0)


class QuantityIn(BaseModel):
    quantity: int = Field(ge=0)


class CheckoutIn(BaseModel):
    payment_method: PaymentMethod
    tender: Decimal | None = Field(default=None, ge=0)


class OrderLineIn(BaseModel):
    book_id: int
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    supplier: str = Field(min_length=1, max_length=255)
    lines: list[OrderLineIn] = Field(min_length=1)


class RequestIn(BaseModel):
    customer_name: str = Field(min_length=1)
    customer_contact: str = Field(min_length=1)
    book_title: str = Field(min_length=1)


class RequestStatusIn(BaseModel):
    status: RequestStatus


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Role
    active: bool


__all__ = [
    "LoginIn",
    "BookIn",
    "BookEdit",
    "BookOut",
    "ReceiveIn",
    "CorrectIn",
    "CartLineIn",
    "QuantityIn",
    "CheckoutIn",
    "OrderIn",
    "OrderLineIn",
    "RequestIn",
    "RequestStatusIn",
    "UserOut",
    "OrderStatus",
]

