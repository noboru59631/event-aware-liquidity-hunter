# Risk Rules

- Target risk: **1%** of equity per trade; hard maximum **1.5%**.
- Size is derived from stop distance, not an AI recommendation.
- Maximum **2** concurrent positions.
- At **3% daily** drawdown, new entries stop. At **5% total** drawdown, the exit guardrail closes risk.
- Entries require **1.5:1** minimum reward/risk and valid ATR.
- High-impact event risk blocks new entries and reduces existing exposure.
- Adaptive logic can tighten, trail, or move a stop to breakeven only; it cannot widen stops or increase size.
- No live trading is enabled by default.
