"""
🌙 Moon Dev's MiroFish Agent
Daily market regime bias via MiroFish swarm-intelligence simulation.

MiroFish (https://github.com/666ghj/MiroFish) simulates thousands of autonomous
market-participant agents reacting to news/macro events to forecast sentiment
direction.  Because each simulation is expensive ($0.50-2.00 in LLM API calls),
this agent runs ONCE PER DAY and caches the result.  The trading agent reads the
cached regime on every 15-minute cycle at zero additional API cost.

Regime → trading_agent.py effect
  "bull":     normal position size × 1.0, consensus threshold ≥ 51%
  "bear":     position size × 0.5,        consensus threshold ≥ 67%
  "sideways": position size × 0.7,        consensus threshold ≥ 60%

Prerequisites
  1. Clone MiroFish:  git clone https://github.com/666ghj/MiroFish /home/user/MiroFish
  2. Configure /home/user/MiroFish/.env (LLM_API_KEY, ZEP_API_KEY, etc.)
  3. Start service:   docker compose up -d      → http://localhost:5001
  4. Set MIROFISH_ENABLED=true in TradingAgent .env

Built with love by Moon Dev 🚀
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from termcolor import cprint
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
MIROFISH_API_URL  = os.getenv("MIROFISH_API_URL", "http://localhost:5001")
MIROFISH_ENABLED  = os.getenv("MIROFISH_ENABLED", "false").lower() == "true"
TTL_HOURS         = int(os.getenv("MIROFISH_TTL_HOURS", "24"))   # cache duration

# Files this agent reads (all already produced by existing agents)
SENTIMENT_CSV     = "src/data/sentiment_history.csv"
FRED_CACHE_DIR    = "src/data/fred_cache"
OHLCV_DIR         = "src/data/ohlcv"

# Output
REGIME_FILE       = "src/data/mirofish_regime.json"

# Regime → position multiplier & consensus threshold
REGIME_CONFIG = {
    "bull":     {"position_multiplier": 1.0,  "consensus_threshold": 0.51},
    "bear":     {"position_multiplier": 0.5,  "consensus_threshold": 0.67},
    "sideways": {"position_multiplier": 0.70, "consensus_threshold": 0.60},
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _is_service_up(timeout: int = 5) -> bool:
    """Return True if MiroFish backend is reachable."""
    try:
        r = requests.get(f"{MIROFISH_API_URL}/api/simulation", timeout=timeout)
        return r.status_code < 500
    except requests.RequestException:
        return False


def _load_regime() -> dict | None:
    """Return cached regime if it exists and is within TTL, else None."""
    path = Path(REGIME_FILE)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.utcnow() - cached_at < timedelta(hours=TTL_HOURS):
            return data
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


def _save_regime(regime: dict):
    """Persist regime with timestamp to REGIME_FILE."""
    regime["cached_at"] = datetime.utcnow().isoformat()
    Path(REGIME_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(REGIME_FILE).write_text(json.dumps(regime, indent=2))
    cprint(f"💾 MiroFish regime cached → {REGIME_FILE}", "green")


# ─── Seed context builder ─────────────────────────────────────────────────────

def build_seed_context() -> str:
    """Aggregate existing data files into a concise text seed for MiroFish.

    Reads from files already produced by SentimentAgent, FRED cache, and OHLCV
    collector — no new data sources required.
    """
    sections = []
    today = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    sections.append(f"=== Market Intelligence Seed — {today} ===\n")

    # 1. Twitter/X Sentiment (last 5 rows of sentiment_history.csv)
    try:
        import pandas as pd
        sentiment_path = Path(SENTIMENT_CSV)
        if sentiment_path.exists():
            df = pd.read_csv(sentiment_path)
            recent = df.tail(5)
            sections.append("--- Recent Market Sentiment (Twitter/X) ---")
            sections.append(recent.to_string(index=False))
            sections.append("")
    except Exception as e:
        sections.append(f"(Sentiment data unavailable: {e})\n")

    # 2. FRED economic indicators (most recent cached files)
    try:
        fred_dir = Path(FRED_CACHE_DIR)
        if fred_dir.exists():
            fred_files = sorted(fred_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
            if fred_files:
                sections.append("--- FRED Economic Indicators ---")
                for f in fred_files:
                    try:
                        data = json.loads(f.read_text())
                        # Take only last observation
                        if isinstance(data, dict):
                            sections.append(f"{f.stem}: {json.dumps(data)[:200]}")
                    except Exception:
                        pass
                sections.append("")
    except Exception as e:
        sections.append(f"(FRED data unavailable: {e})\n")

    # 3. OHLCV summary — last 3 closes per token
    try:
        import pandas as pd
        ohlcv_dir = Path(OHLCV_DIR)
        if ohlcv_dir.exists():
            csv_files = sorted(ohlcv_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)[:4]
            if csv_files:
                sections.append("--- Recent Price Action (last 3 bars) ---")
                for f in csv_files:
                    try:
                        df = pd.read_csv(f, index_col=0).tail(3)
                        sections.append(f"{f.stem}:")
                        sections.append(df[["open", "high", "low", "close", "volume"]].to_string() if all(
                            c in df.columns for c in ["open", "high", "low", "close", "volume"]
                        ) else df.to_string())
                    except Exception:
                        pass
                sections.append("")
    except Exception as e:
        sections.append(f"(OHLCV data unavailable: {e})\n")

    sections.append(
        "--- Prediction Task ---\n"
        "Based on the above market intelligence, forecast the most likely short-term "
        "market direction for crypto and equities over the next 24 hours.  "
        "Return a probability-weighted assessment: bullish, bearish, or sideways."
    )

    return "\n".join(sections)


# ─── MiroFish API calls ───────────────────────────────────────────────────────

def _post(path: str, payload: dict, timeout: int = 60) -> dict | None:
    """POST to MiroFish backend and return JSON response, or None on error."""
    url = f"{MIROFISH_API_URL}{path}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        cprint(f"❌ MiroFish API error ({path}): {e}", "red")
        return None


def _get(path: str, timeout: int = 30) -> dict | None:
    """GET from MiroFish backend."""
    url = f"{MIROFISH_API_URL}{path}"
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        cprint(f"❌ MiroFish API error ({path}): {e}", "red")
        return None


def query_mirofish(seed_context: str) -> dict:
    """Send seed to MiroFish and return a parsed regime dict.

    Flow:
      1. Create a project and build the knowledge graph
      2. Start a short simulation (≤ 20 rounds to control cost)
      3. Generate a report
      4. Parse direction from report summary

    Returns:
        {direction, confidence, narrative, horizon} or fallback neutral regime
    """
    FALLBACK = {"direction": "sideways", "confidence": 0.5,
                "narrative": "MiroFish unavailable — using neutral fallback",
                "horizon": "24h"}

    cprint("🐟 Querying MiroFish simulation API...", "cyan")

    # Step 1: Create graph project with seed
    project = _post("/api/graph/build", {
        "seed_text": seed_context,
        "ontology": "financial_markets",   # MiroFish will default if not found
    }, timeout=120)

    if not project:
        cprint("⚠️ MiroFish: failed to build graph — using neutral fallback", "yellow")
        return FALLBACK

    project_id = project.get("project_id") or project.get("id")
    if not project_id:
        cprint("⚠️ MiroFish: no project_id in response — using neutral fallback", "yellow")
        return FALLBACK

    cprint(f"✅ MiroFish graph built (project_id={project_id})", "green")

    # Step 2: Start simulation (short, ≤ 20 rounds)
    sim = _post("/api/simulation/create", {
        "project_id": project_id,
        "max_rounds": 20,
        "prediction_task": "short-term market direction (24h)",
    }, timeout=60)

    if not sim:
        return FALLBACK

    sim_id = sim.get("simulation_id") or sim.get("id")
    if not sim_id:
        return FALLBACK

    start_result = _post(f"/api/simulation/{sim_id}/start", {}, timeout=30)
    if not start_result:
        return FALLBACK

    cprint(f"🔄 MiroFish simulation running (id={sim_id})... this may take a few minutes", "cyan")

    # Step 3: Poll for completion (up to 10 min)
    for attempt in range(60):
        time.sleep(10)
        status_data = _get(f"/api/simulation/{sim_id}")
        if not status_data:
            break
        status = status_data.get("status", "running")
        cprint(f"   ⏳ Simulation status: {status} (poll {attempt + 1}/60)", "white")
        if status in ("completed", "done", "finished"):
            break
        if status in ("failed", "error"):
            cprint("❌ MiroFish simulation failed", "red")
            return FALLBACK

    # Step 4: Generate report
    report = _post(f"/api/report/generate", {"simulation_id": sim_id}, timeout=120)
    if not report:
        return FALLBACK

    # Step 5: Parse direction from report text
    report_text = (
        report.get("summary") or
        report.get("narrative") or
        report.get("report") or
        str(report)
    ).lower()

    bull_keywords  = ["bullish", "upward", "positive", "rally", "growth", "rise", "increase"]
    bear_keywords  = ["bearish", "downward", "negative", "decline", "fall", "drop", "decrease", "risk-off"]

    bull_score = sum(report_text.count(k) for k in bull_keywords)
    bear_score = sum(report_text.count(k) for k in bear_keywords)
    total       = bull_score + bear_score + 1  # avoid div/0

    if bull_score > bear_score and bull_score / total > 0.4:
        direction = "bull"
        confidence = min(0.95, 0.5 + bull_score / (total * 2))
    elif bear_score > bull_score and bear_score / total > 0.4:
        direction = "bear"
        confidence = min(0.95, 0.5 + bear_score / (total * 2))
    else:
        direction  = "sideways"
        confidence = 0.55

    narrative = (
        report.get("summary") or
        report.get("narrative") or
        "MiroFish simulation completed."
    )[:500]

    result = {
        "direction":  direction,
        "confidence": round(confidence, 3),
        "narrative":  narrative,
        "horizon":    "24h",
        "sim_id":     sim_id,
    }

    cprint(f"🎯 MiroFish regime: {direction.upper()} (confidence={confidence:.0%})", "cyan", attrs=["bold"])
    return result


# ─── Main agent class ─────────────────────────────────────────────────────────

class MiroFishAgent:
    """Daily market regime simulation agent powered by MiroFish."""

    def get_regime(self) -> dict | None:
        """Return cached regime dict, or None if stale/unavailable.

        Keys: direction, confidence, narrative, horizon, cached_at
        """
        return _load_regime()

    def should_run(self) -> bool:
        """True only if regime cache is stale (> TTL hours old)."""
        return _load_regime() is None

    def run(self):
        """Run MiroFish simulation if cache is stale; no-op otherwise."""
        if not MIROFISH_ENABLED:
            cprint("🐟 MiroFish disabled (MIROFISH_ENABLED=false) — skipping", "white")
            return

        if not self.should_run():
            cached = _load_regime()
            direction = cached.get("direction", "?") if cached else "?"
            cprint(f"🐟 MiroFish regime cache is fresh ({direction}) — skipping simulation", "white")
            return

        if not _is_service_up():
            cprint(
                "⚠️ MiroFish service not reachable at " + MIROFISH_API_URL +
                " — ensure Docker is running (docker compose up -d in MiroFish repo)",
                "yellow"
            )
            return

        cprint("\n🐟 MiroFish: building seed context from existing data...", "cyan")
        seed = build_seed_context()
        cprint(f"📄 Seed context length: {len(seed)} chars", "white")

        regime = query_mirofish(seed)
        _save_regime(regime)

        direction  = regime["direction"]
        confidence = regime["confidence"]
        cfg        = REGIME_CONFIG.get(direction, REGIME_CONFIG["sideways"])
        cprint(
            f"\n🌊 MiroFish Regime: {direction.upper()} | "
            f"Confidence: {confidence:.0%} | "
            f"Position multiplier: ×{cfg['position_multiplier']} | "
            f"Consensus threshold: ≥{cfg['consensus_threshold']:.0%}",
            "cyan", attrs=["bold"]
        )


# ─── Utility for trading_agent.py ────────────────────────────────────────────

def load_mirofish_regime() -> dict | None:
    """Return the latest cached regime dict, or None.

    Call this from trading_agent.py before each trade cycle:
        from src.agents.mirofish_agent import load_mirofish_regime, REGIME_CONFIG
        regime = load_mirofish_regime()
    """
    return _load_regime()


if __name__ == "__main__":
    # Run standalone for testing
    agent = MiroFishAgent()
    agent.run()
    regime = agent.get_regime()
    if regime:
        print(json.dumps(regime, indent=2))
