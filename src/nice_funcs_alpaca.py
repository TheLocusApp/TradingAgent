"""
🌙 Moon Dev's Alpaca Trading Functions
Alpaca Markets broker integration for US stocks & ETFs.
Inspired by TradingView-Claw's broker_client.py pattern.

Alpaca supports:
  - Commission-free US stocks and ETFs
  - Paper trading (sandbox) and live trading
  - Fractional shares
  - Extended hours trading

Setup:
  1. Create account at https://alpaca.markets
  2. Get API key from dashboard (paper or live)
  3. Set ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL in .env

Built with love by Moon Dev 🚀
"""

import os
import time
from termcolor import cprint
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
ALPACA_API_KEY  = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
# Paper trading URL (default); switch to https://api.alpaca.markets for live
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# ─── Client factory ───────────────────────────────────────────────────────────

def get_alpaca_client():
    """Return an authenticated Alpaca REST client.

    Requires alpaca-trade-api:  pip install alpaca-trade-api
    """
    try:
        import alpaca_trade_api as tradeapi  # noqa: F401 — checked at call site
    except ImportError:
        cprint("❌ alpaca-trade-api not installed. Run: pip install alpaca-trade-api", "red")
        raise

    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise ValueError(
            "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env. "
            "Get them from https://app.alpaca.markets/paper-account/overview"
        )

    import alpaca_trade_api as tradeapi
    client = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)
    cprint(f"✅ Alpaca client connected ({ALPACA_BASE_URL})", "green")
    return client


# ─── Account ──────────────────────────────────────────────────────────────────

def get_account_balance() -> float:
    """Return available cash balance in USD."""
    try:
        client = get_alpaca_client()
        account = client.get_account()
        balance = float(account.cash)
        cprint(f"💰 Alpaca Cash Balance: ${balance:,.2f}", "cyan")
        return balance
    except Exception as e:
        cprint(f"❌ Error getting Alpaca balance: {e}", "red")
        return 0.0


def get_account_value() -> float:
    """Return total portfolio value (cash + positions)."""
    try:
        client = get_alpaca_client()
        account = client.get_account()
        value = float(account.portfolio_value)
        cprint(f"💎 Alpaca Portfolio Value: ${value:,.2f}", "cyan")
        return value
    except Exception as e:
        cprint(f"❌ Error getting Alpaca portfolio value: {e}", "red")
        return 0.0


# ─── Orders ───────────────────────────────────────────────────────────────────

def place_market_order(symbol: str, notional_usd: float, side: str) -> dict:
    """Place a notional market order (buy/sell $X worth of a symbol).

    Args:
        symbol:       Ticker symbol, e.g. "AAPL", "SPY"
        notional_usd: Dollar amount to buy or sell
        side:         "buy" or "sell"

    Returns:
        Order dict from Alpaca, or {} on failure
    """
    try:
        client = get_alpaca_client()
        cprint(f"📤 Alpaca {side.upper()} ${notional_usd:,.2f} of {symbol}", "yellow", attrs=["bold"])

        order = client.submit_order(
            symbol=symbol,
            notional=round(notional_usd, 2),
            side=side,
            type="market",
            time_in_force="day",
        )

        cprint(f"✅ Order submitted: {order.id} | {side.upper()} ${notional_usd:,.2f} {symbol}", "green")
        return order._raw  # type: ignore[attr-defined]
    except Exception as e:
        cprint(f"❌ Alpaca order error ({side} {symbol}): {e}", "red")
        return {}


def market_buy(symbol: str, usd_amount: float, **kwargs) -> dict:
    """Buy $usd_amount of symbol at market price."""
    return place_market_order(symbol, usd_amount, "buy")


def market_sell(symbol: str, usd_amount: float, **kwargs) -> dict:
    """Sell $usd_amount of symbol at market price.

    Note: Alpaca does not support shorting on paper accounts by default.
    For live accounts, short selling requires margin approval.
    """
    return place_market_order(symbol, usd_amount, "sell")


def ai_entry(symbol: str, usd_amount: float, **kwargs) -> bool:
    """AI-guided entry wrapper (matches the nice_funcs interface).

    Returns True if order was placed successfully.
    """
    result = market_buy(symbol, usd_amount)
    return bool(result)


# ─── Positions ────────────────────────────────────────────────────────────────

def get_position(symbol: str) -> dict:
    """Return normalised position dict for symbol.

    Returns a dict with keys matching the exchange_manager interface:
        has_position, size, symbol, entry_price, pnl_percent, is_long
    """
    try:
        client = get_alpaca_client()
        pos = client.get_position(symbol)
        entry_px = float(pos.avg_entry_price)
        current_px = float(pos.current_price)
        pnl_pct = ((current_px - entry_px) / entry_px) * 100 if entry_px else 0

        return {
            "has_position": True,
            "size": float(pos.qty),
            "symbol": symbol,
            "entry_price": entry_px,
            "pnl_percent": round(pnl_pct, 2),
            "is_long": float(pos.qty) > 0,
            "market_value": float(pos.market_value),
            "unrealized_pl": float(pos.unrealized_pl),
        }
    except Exception:
        # Position not found → no open position
        return {
            "has_position": False,
            "size": 0,
            "symbol": symbol,
            "entry_price": 0,
            "pnl_percent": 0,
            "is_long": True,
            "market_value": 0,
            "unrealized_pl": 0,
        }


def get_open_positions() -> list:
    """Return a list of all open positions as normalised dicts."""
    try:
        client = get_alpaca_client()
        positions = client.list_positions()
        return [
            {
                "symbol": p.symbol,
                "size": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "pnl_percent": round(
                    (float(p.current_price) - float(p.avg_entry_price))
                    / float(p.avg_entry_price) * 100, 2
                ) if float(p.avg_entry_price) else 0,
                "is_long": float(p.qty) > 0,
            }
            for p in positions
        ]
    except Exception as e:
        cprint(f"❌ Error listing Alpaca positions: {e}", "red")
        return []


def get_token_balance_usd(symbol: str) -> float:
    """Return current USD market value of position in symbol."""
    pos = get_position(symbol)
    return pos.get("market_value", 0.0)


def close_position(symbol: str) -> dict:
    """Close the entire position in symbol at market price."""
    try:
        client = get_alpaca_client()
        cprint(f"🔴 Closing Alpaca position: {symbol}", "yellow", attrs=["bold"])
        result = client.close_position(symbol)
        cprint(f"✅ Position closed: {symbol}", "green")
        return result._raw  # type: ignore[attr-defined]
    except Exception as e:
        cprint(f"❌ Error closing Alpaca position ({symbol}): {e}", "red")
        return {}


def kill_switch(symbol: str, **kwargs) -> dict:
    """Alias for close_position — matches the kill_switch interface."""
    return close_position(symbol)


def chunk_kill(symbol: str, max_usd_order_size: float = 100, slippage: int = 0, **kwargs) -> dict:
    """Close position. Alpaca handles partial fills natively, so no chunking needed."""
    return close_position(symbol)


# ─── Price data ───────────────────────────────────────────────────────────────

def get_current_price(symbol: str) -> float:
    """Return latest trade price for symbol."""
    try:
        client = get_alpaca_client()
        trade = client.get_latest_trade(symbol)
        price = float(trade.price)
        cprint(f"💲 {symbol} = ${price:,.4f}", "white")
        return price
    except Exception as e:
        cprint(f"❌ Error getting Alpaca price for {symbol}: {e}", "red")
        return 0.0


# ─── Symbols for Alpaca (US stocks/ETFs) ─────────────────────────────────────
# Use ticker symbols like "AAPL", "SPY", "QQQ", "MSFT", etc.
# These are set in trading_agent.py SYMBOLS list when EXCHANGE = "ALPACA"
