#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:
    # Market BUY
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

    # Limit SELL
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

    # Stop-Market BUY (bonus order type)
    python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 65000

Credentials are read from environment variables:
    BINANCE_API_KEY
    BINANCE_API_SECRET

Or pass them explicitly via --api-key / --api-secret flags.
"""

from __future__ import annotations

import argparse
import os
import sys

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import place_order


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Credentials (optional — fall back to env vars)
    creds = parser.add_argument_group("credentials (can also be set via env vars)")
    creds.add_argument(
        "--api-key",
        default=None,
        help="Binance API key (default: $BINANCE_API_KEY).",
    )
    creds.add_argument(
        "--api-secret",
        default=None,
        help="Binance API secret (default: $BINANCE_API_SECRET).",
    )

    # Order parameters
    order = parser.add_argument_group("order parameters")
    order.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol, e.g. BTCUSDT.",
    )
    order.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        help="Order side: BUY or SELL.",
    )
    order.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        type=str.upper,
        help="Order type: MARKET, LIMIT, or STOP_MARKET.",
    )
    order.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (e.g. 0.001 for BTC).",
    )
    order.add_argument(
        "--price",
        default=None,
        help="Limit price — required for LIMIT orders.",
    )
    order.add_argument(
        "--stop-price",
        default=None,
        dest="stop_price",
        help="Stop trigger price — required for STOP_MARKET orders.",
    )

    # Misc
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory to write log files (default: ./logs).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print DEBUG-level logs to the console as well.",
    )

    return parser


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """Return (api_key, api_secret) from args or env, or exit with an error."""
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    missing = []
    if not api_key:
        missing.append("BINANCE_API_KEY (use --api-key or set the env var)")
    if not api_secret:
        missing.append("BINANCE_API_SECRET (use --api-secret or set the env var)")

    if missing:
        print("\n[ERROR] Missing credentials:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)

    return api_key, api_secret


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_dir=args.log_dir, log_level=log_level)

    if args.verbose:
        # Promote console handler to DEBUG
        for h in logger.handlers:
            if hasattr(h, "stream"):
                h.setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Trading bot started")
    logger.info("CLI args: symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
                args.symbol, args.side, args.order_type,
                args.quantity, args.price, args.stop_price)

    api_key, api_secret = resolve_credentials(args)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    try:
        result = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        print(f"\n[VALIDATION ERROR] {exc}", file=sys.stderr)
        logger.error("Validation error: %s", exc)
        sys.exit(2)
    except BinanceAPIError as exc:
        print(f"\n[API ERROR] {exc}", file=sys.stderr)
        logger.error("API error: %s", exc)
        sys.exit(3)
    except ConnectionError as exc:
        print(f"\n[NETWORK ERROR] {exc}", file=sys.stderr)
        logger.error("Network error: %s", exc)
        sys.exit(4)
    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR] {exc}", file=sys.stderr)
        logger.exception("Unexpected error: %s", exc)
        sys.exit(99)

    # Success — print result
    print(result.display_summary())

    if result.is_filled():
        print("\n✅  Order FILLED successfully!")
    else:
        print(f"\n✅  Order placed — current status: {result.status}")

    logger.info("Trading bot finished successfully — orderId=%s", result.order_id)


if __name__ == "__main__":
    main()
