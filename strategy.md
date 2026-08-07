# Event-Aware Liquidity Hunter — Botcamp Submission

## Overview

A prototype autonomous decision engine for liquid Hyperliquid perpetual markets. Its core principle is: **entry is rule-based, exit is AI/event-aware, risk is deterministic**.

## Market hypothesis

Liquid crypto markets frequently sweep visible liquidity before reverting toward the trend. Fixed TP/SL exits discard new information once a trade is open. Momentum, volatility, and public statements can change an open trade’s quality rapidly.

## Why this is different

This is not another EMA/RSI bot. EMA and RSI confirm a liquidity-sweep entry; the differentiator is an adaptive exit layer that scores acceleration, candle direction, RSI, ATR, event sentiment, and impact. It is deterministic and auditable—not an external LLM—and cannot override risk constraints.

## Entry logic

Long: bullish sweep, bullish/neutral EMA trend, non-extreme RSI, valid ATR, >=1.5 reward/risk, and risk approval. Short rules are symmetric.

## Event-aware exits and news

Favorable aligned context may hold or trail. Profit can move the stop to breakeven. Adverse context takes partial profit or exits. High-impact public events—central banks, regulators, exchange executives, or political leaders—tighten risk. Future data adapters can provide events; this prototype makes no calls.

## Risk and no-trade conditions

1% equity risk, hard 1.5% cap, two positions maximum, 3% daily stop, 5% total stop, ATR boundaries, insufficient data, poor reward/risk, and high event risk all block entries. The adaptive layer cannot add size or widen a stop.

## Competition goal and future improvements

Demonstrate safe, composable adaptive exit management for later paper-first integration with Hummingbot Condor or Hyperliquid. Next: event feeds, backtesting, persistent state, and audited paper execution.
