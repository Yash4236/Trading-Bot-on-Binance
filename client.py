"""
Binance Futures Testnet REST client.

Wraps the low-level HTTP requests, handles HMAC-SHA256 signing,
timestamps, and uniform error surfacing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
_DEFAULT_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Minimal Binance USDT-M Futures REST client.

    Args:
        api_key: Binance Futures Testnet API key.
        api_secret: Binance Futures Testnet API secret.
        base_url: Base URL (defaults to testnet).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must both be provided.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised against %s", self._base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append HMAC-SHA256 signature to params dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    @staticmethod
    def _timestamp() -> int:
        return int(time.time() * 1000)

    def _post(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign and POST to an endpoint; return parsed JSON."""
        params["timestamp"] = self._timestamp()
        params = self._sign(params)
        url = f"{self._base_url}{endpoint}"

        logger.debug("POST %s  params=%s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self._session.post(url, data=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            logger.error("Request to %s timed out after %ds", url, self._timeout)
            raise ConnectionError(f"Request timed out after {self._timeout}s.")
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error reaching %s: %s", url, exc)
            raise ConnectionError(f"Network error: {exc}") from exc

        logger.debug("Response %s  body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response from %s: %s", url, response.text[:200])
            raise BinanceAPIError(-1, f"Non-JSON response: {response.text[:200]}")

        if not response.ok or (isinstance(data, dict) and "code" in data and data["code"] < 0):
            code = data.get("code", response.status_code) if isinstance(data, dict) else response.status_code
            msg = data.get("msg", response.text) if isinstance(data, dict) else response.text
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: str = "GTC",
        stop_price: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a new futures order.

        Args:
            symbol: Trading pair, e.g. 'BTCUSDT'.
            side: 'BUY' or 'SELL'.
            order_type: 'MARKET', 'LIMIT', or 'STOP_MARKET'.
            quantity: Order quantity as string.
            price: Required for LIMIT orders.
            time_in_force: 'GTC', 'IOC', 'FOK' (LIMIT only, default 'GTC').
            stop_price: Required for STOP_MARKET orders.

        Returns:
            Raw order response dict from Binance.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if not price:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if not stop_price:
                raise ValueError("stopPrice is required for STOP_MARKET orders.")
            params["stopPrice"] = stop_price

        logger.info(
            "Placing order — symbol=%s side=%s type=%s qty=%s price=%s",
            symbol, side, order_type, quantity, price or stop_price or "N/A",
        )

        result = self._post("/fapi/v1/order", params)
        logger.info("Order placed successfully — orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_account(self) -> Dict[str, Any]:
        """Return futures account information (useful for connectivity checks)."""
        params: Dict[str, Any] = {"timestamp": self._timestamp()}
        params = self._sign(params)
        url = f"{self._base_url}/fapi/v2/account"
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            return response.json()
        except Exception as exc:
            logger.error("get_account failed: %s", exc)
            raise
