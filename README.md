# Event-Aware Liquidity Hunter

Offline-safe prototype for BTC-USD, ETH-USD, and SOL-USD perpetuals. It contains no exchange, network, private-key, or order-execution code.

## The edge: adaptive exits

Entries are deterministic: liquidity sweep, EMA trend, RSI, ATR, risk/reward, and account checks. Exits adapt through transparent momentum and event scoring, selecting HOLD, partial profit, breakeven, trailing/tightened stop, or full exit. **Risk remains deterministic**: the adaptive layer cannot increase position size, widen the stop beyond original risk, or bypass drawdown limits.

## Entry and exit

A long requires a sweep below recent lows followed by a reclaim, bullish/neutral EMA trend, non-extreme RSI, tradable ATR, and at least 1.5 reward/risk. Shorts mirror the rule above recent highs. Favorable momentum and events can trail a stop; adverse or high-impact context reduces risk.

## Guardrails

- 1% target risk per trade; 1.5% hard maximum
- Two concurrent positions maximum
- Stop new trades at 3% daily or 5% total drawdown
- High event risk blocks new entries; stops only move toward safety
- Live trading is disabled by design

## Run

```powershell
cd C:\Users\jhjop\event-aware-liquidity-hunter
python examples\sample_run.py
```

The sample uses generated candles and fabricated events only. A future Hummingbot Condor or Hyperliquid adapter can consume the returned decision dictionaries.
