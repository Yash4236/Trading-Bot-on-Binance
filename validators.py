"""
Input validation for trading bot CLI parameters.
All validation raises ValueError with a human-readable message on failure.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

# Binance symbol pattern: uppercase letters only, e.g. BTCUSDT
_SYMBOL_RE = re.compile(r"^[A-Z]{2,20}$")


def validate_symbol(symbol: str) -> str:
    """Return uppercased symbol or raise ValueError."""
    sym = symbol.strip().upper()
    if not _SYMBOL_RE.match(sym):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Expected uppercase letters only (e.g. BTCUSDT)."
        )
    return sym


def validate_side(side: str) -> str:
    """Return uppercased side or raise ValueError."""
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return s


def validate_order_type(order_type: str) -> str:
    """Return uppercased order type or raise ValueError."""
    ot = order_type.strip().upper()
    if ot not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return ot


def validate_quantity(quantity: str | float) -> Decimal:
    """Return Decimal quantity or raise ValueError."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price field.

    - LIMIT orders require a positive price.
    - MARKET orders must NOT supply a price.
    - STOP_MARKET orders require a stop price (passed as price).

    Returns Decimal price or None.
    """
    ot = order_type.strip().upper()

    if price is None or price == "":
        if ot == "LIMIT":
            raise ValueError("Price is required for LIMIT orders.")
        if ot == "STOP_MARKET":
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        return None

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")

    if ot == "MARKET":
        raise ValueError("Price must NOT be specified for MARKET orders.")

    return p


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
) -> dict:
    """
    Run all validators and return a clean params dict.

    Raises ValueError on the first validation failure.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type),
    }
