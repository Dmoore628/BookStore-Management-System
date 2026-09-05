"""Enumerations used across the domain."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Staff roles, ordered from most to least privileged."""

    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"


class StockReason(StrEnum):
    """Why a stock movement happened (append-only ledger)."""

    INITIAL = "initial"
    RECEIVE = "receive"
    SALE = "sale"
    CORRECTION = "correction"


class OrderStatus(StrEnum):
    PENDING = "pending"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class RequestStatus(StrEnum):
    NEW = "new"
    ORDERED = "ordered"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
