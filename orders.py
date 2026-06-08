"""
Order placement orchestration layer.

Sits between the CLI and the BinanceClient — validates inputs,
calls the client, and formats the response for display.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import validate_all

logger = logging.getLogger("trading_bot.orders")


class OrderResult:
    """Structured wrapper around a raw Binance order response."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self.raw = raw
        self.order_id: int = raw.get("orderId", 0)
        self.symbol: str = raw.get("symbol", "")
        self.side: str = raw.get("side", "")
        self.order_type: str = raw.get("type", "")
        self.status: str = raw.get("status", "")
        self.orig_qty: str = raw.get("origQty", "")
        self.executed_qty: str = raw.get("executedQty", "0")
        self.avg_price: str = raw.get("avgPrice", "0")
        self.price: str = raw.get("price", "0")
        self.time_in_force: str = raw.get("timeInForce", "")
        self.update_time: int = raw.get("updateTime", 0)

    def is_filled(self) -> bool:
        return self.status == "FILLED"

    def display_summary(self) -> str:
        """Return a formatted multi-line summary string."""
        avg = self.avg_price if self.avg_price not in ("0", "0.0", "") else "N/A"
        limit_price = self.price if self.price not in ("0", "0.0", "") else "N/A"
        lines = [
            "─" * 52,
            "  ORDER RESPONSE",
            "─" * 52,
            f"  Order ID       : {self.order_id}",
            f"  Symbol         : {self.symbol}",
            f"  Side           : {self.side}",
            f"  Type           : {self.order_type}",
            f"  Status         : {self.status}",
            f"  Orig Quantity  : {self.orig_qty}",
            f"  Executed Qty   : {self.executed_qty}",
            f"  Avg Fill Price : {avg}",
            f"  Limit Price    : {limit_price}",
            f"  Time-in-Force  : {self.time_in_force or 'N/A'}",
            "─" * 52,
        ]
        return "\n".join(lines)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
) -> OrderResult:
    """
    Validate inputs, place an order, and return an OrderResult.

    Args:
        client: Authenticated BinanceClient instance.
        symbol: E.g. 'BTCUSDT'.
        side: 'BUY' or 'SELL'.
        order_type: 'MARKET', 'LIMIT', or 'STOP_MARKET'.
        quantity: Order quantity.
        price: Limit price (LIMIT orders only).
        stop_price: Stop trigger price (STOP_MARKET orders only).

    Returns:
        OrderResult wrapping the Binance response.

    Raises:
        ValueError: On invalid input.
        BinanceAPIError: On API-level failures.
        ConnectionError: On network failures.
    """
    # For STOP_MARKET, pass stop_price through the price validator slot
    effective_price = stop_price if order_type.upper() == "STOP_MARKET" else price

    validated = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=effective_price,
    )

    sym = validated["symbol"]
    s = validated["side"]
    ot = validated["order_type"]
    qty = str(validated["quantity"])
    p = str(validated["price"]) if validated["price"] is not None else None

    # Print request summary to stdout
    _print_request_summary(sym, s, ot, qty, price=p if ot == "LIMIT" else None, stop_price=p if ot == "STOP_MARKET" else None)

    logger.debug(
        "Validated order params — symbol=%s side=%s type=%s qty=%s price=%s",
        sym, s, ot, qty, p,
    )

    raw_response = client.place_order(
        symbol=sym,
        side=s,
        order_type=ot,
        quantity=qty,
        price=p if ot == "LIMIT" else None,
        stop_price=p if ot == "STOP_MARKET" else None,
    )

    result = OrderResult(raw_response)
    logger.info("Order result — %s", result.display_summary().replace("\n", " | "))
    return result


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> None:
    lines = [
        "─" * 52,
        "  ORDER REQUEST SUMMARY",
        "─" * 52,
        f"  Symbol         : {symbol}",
        f"  Side           : {side}",
        f"  Type           : {order_type}",
        f"  Quantity       : {quantity}",
    ]
    if price:
        lines.append(f"  Limit Price    : {price}")
    if stop_price:
        lines.append(f"  Stop Price     : {stop_price}")
    lines.append("─" * 52)
    print("\n".join(lines))
