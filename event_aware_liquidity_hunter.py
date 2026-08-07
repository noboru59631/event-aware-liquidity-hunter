"""Offline, risk-bounded crypto perpetual decision engine. No network or order execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from statistics import mean
from typing import Literal

@dataclass(frozen=True)
class Candle:
    timestamp: str; open: float; high: float; low: float; close: float; volume: float
@dataclass(frozen=True)
class MarketEvent:
    timestamp: str; event_type: str; title: str; description: str; sentiment_score: float; impact_score: float; source: str; related_assets: list[str] = field(default_factory=list)
@dataclass
class Position:
    symbol: str; side: Literal['LONG','SHORT']; entry_price: float; current_price: float; size: float; stop_loss: float; take_profit: float; unrealized_pnl_pct: float; opened_at: str
@dataclass(frozen=True)
class StrategyConfig:
    ema_fast:int=50; ema_slow:int=200; atr_period:int=14; rsi_period:int=14; liquidity_lookback:int=20
    risk_per_trade:float=.01; max_risk_per_trade:float=.015; max_concurrent_positions:int=2
    daily_drawdown_stop:float=.03; total_drawdown_stop:float=.05; min_risk_reward:float=1.5
    atr_stop_multiplier:float=1.2; atr_take_profit_multiplier:float=2.; atr_extended_take_profit_multiplier:float=3.
    min_atr_pct:float=.001; max_atr_pct:float=.05; event_risk_threshold:float=.7
    momentum_extension_threshold:float=.65; momentum_exhaustion_threshold:float=-.4

class EventAwareLiquidityHunter:
    """Deterministic entries plus transparent, guardrail-constrained adaptive exits."""
    def __init__(self, config:StrategyConfig|None=None): self.config=config or StrategyConfig()
    @staticmethod
    def ema(v:list[float], p:int)->float:
        if len(v)<p: raise ValueError('Not enough values for EMA')
        x=mean(v[:p]); k=2/(p+1)
        for n in v[p:]: x=(n-x)*k+x
        return x
    @staticmethod
    def atr(c:list[Candle], p:int)->float:
        if len(c)<p+1: raise ValueError('Not enough candles for ATR')
        return mean(max(x.high-x.low,abs(x.high-y.close),abs(x.low-y.close)) for y,x in zip(c[-p-1:-1],c[-p:]))
    @staticmethod
    def rsi(v:list[float], p:int)->float:
        if len(v)<p+1: raise ValueError('Not enough closes for RSI')
        d=[b-a for a,b in zip(v[-p-1:-1],v[-p:])]; gain=mean(max(x,0) for x in d); loss=mean(max(-x,0) for x in d)
        return 100. if loss==0 else 100-100/(1+gain/loss)
    @staticmethod
    def momentum_score(c:list[Candle])->float:
        if len(c)<6:return 0.
        r=[(b.close-a.close)/a.close for a,b in zip(c[-6:-1],c[-5:])]; direct=sum(1 if x.close>x.open else -1 if x.close<x.open else 0 for x in c[-4:])/4
        return max(-1.,min(1.,.65*direct+50*mean(r)+100*(r[-1]-mean(r[:-1]))))
    def volatility_score(self,c:list[Candle])->float: return min(1.,self.atr(c,self.config.atr_period)/c[-1].close/self.config.max_atr_pct)
    def liquidity_sweep(self,c:list[Candle])->str:
        n=self.config.liquidity_lookback
        if len(c)<n+1:return 'NONE'
        cur,old=c[-1],c[-n-1:-1]; lo=min(x.low for x in old); hi=max(x.high for x in old)
        if cur.low<lo and cur.close>lo:return 'BULLISH'
        if cur.high>hi and cur.close<hi:return 'BEARISH'
        return 'NONE'
    def risk_check(self,daily_drawdown:float,total_drawdown:float,open_positions:int)->dict:
        if daily_drawdown>=self.config.daily_drawdown_stop:return {'passed':False,'reason':'daily drawdown stop reached'}
        if total_drawdown>=self.config.total_drawdown_stop:return {'passed':False,'reason':'total drawdown stop reached'}
        if open_positions>=self.config.max_concurrent_positions:return {'passed':False,'reason':'maximum concurrent positions reached'}
        return {'passed':True,'reason':'risk checks passed'}
    def decide_entry(self,symbol:str,candles:list[Candle],account_equity:float,daily_drawdown:float,total_drawdown:float,open_positions:int)->dict:
        base={'action':'FLAT','symbol':symbol,'entry':None,'stop_loss':None,'take_profit':None,'position_size':0.,'risk_reward':0.}
        if len(candles)<max(self.config.ema_slow,self.config.liquidity_lookback+1,self.config.atr_period+1): return base|{'reason':'insufficient data','market_state':'UNKNOWN'}
        check=self.risk_check(daily_drawdown,total_drawdown,open_positions)
        if not check['passed']:return base|{'reason':check['reason'],'market_state':'RISK_OFF'}
        close=[x.close for x in candles]; fast,slow=self.ema(close,self.config.ema_fast),self.ema(close,self.config.ema_slow); state='BULLISH' if fast>slow else 'BEARISH' if fast<slow else 'NEUTRAL'
        atr=self.atr(candles,self.config.atr_period); ap=atr/close[-1]
        if not self.config.min_atr_pct<=ap<=self.config.max_atr_pct:return base|{'reason':'volatility too low' if ap<self.config.min_atr_pct else 'volatility too high','market_state':state}
        sweep=self.liquidity_sweep(candles); r=self.rsi(close,self.config.rsi_period); side='LONG' if sweep=='BULLISH' and state in ('BULLISH','NEUTRAL') and r<75 else 'SHORT' if sweep=='BEARISH' and state in ('BEARISH','NEUTRAL') and r>25 else 'FLAT'
        if side=='FLAT':return base|{'reason':'no qualifying liquidity setup','market_state':state}
        entry=close[-1]; stop=entry-atr*self.config.atr_stop_multiplier if side=='LONG' else entry+atr*self.config.atr_stop_multiplier; target=entry+atr*self.config.atr_take_profit_multiplier if side=='LONG' else entry-atr*self.config.atr_take_profit_multiplier; rr=abs(target-entry)/abs(entry-stop)
        if rr<self.config.min_risk_reward:return base|{'reason':'risk-reward too poor','market_state':state}
        size=account_equity*min(self.config.risk_per_trade,self.config.max_risk_per_trade)/abs(entry-stop)
        return {'action':side,'reason':'qualified liquidity sweep with deterministic risk sizing','symbol':symbol,'entry':entry,'stop_loss':stop,'take_profit':target,'position_size':size,'risk_reward':round(rr,2),'market_state':state}
    def analyze_event_context(self,p:Position,events:list[MarketEvent])->dict:
        asset=p.symbol.split('-')[0]; e=[x for x in events if not x.related_assets or asset in x.related_assets]
        if not e:return {'score':0.,'risk':0.,'summary':'no relevant events'}
        raw=mean(x.sentiment_score*x.impact_score for x in e); return {'score':raw if p.side=='LONG' else -raw,'risk':max(x.impact_score for x in e),'summary':f'{len(e)} relevant event(s)'}
    def analyze_momentum_context(self,p:Position,c:list[Candle])->dict:
        raw=self.momentum_score(c); return {'score':raw if p.side=='LONG' else -raw,'raw_score':raw,'rsi':self.rsi([x.close for x in c],self.config.rsi_period),'volatility':self.volatility_score(c)}
    @staticmethod
    def _safer_stop(p:Position,f:float)->float:
        candidate=p.entry_price+(p.current_price-p.entry_price)*f
        return max(p.stop_loss,candidate) if p.side=='LONG' else min(p.stop_loss,candidate)
    def dynamic_exit_policy(self,p:Position,m:dict,e:dict,daily:float,total:float)->dict:
        if daily>=self.config.daily_drawdown_stop or total>=self.config.total_drawdown_stop:return {'action':'EXIT_FULL','reason':'drawdown guardrail reached','new_stop_loss':p.stop_loss}
        if e['risk']>=self.config.event_risk_threshold:return {'action':'EXIT_FULL' if e['score']<-.35 else 'TIGHTEN_STOP','reason':'high-impact event risk','new_stop_loss':self._safer_stop(p,.5)}
        score=.6*m['score']+.4*e['score']
        if score<=self.config.momentum_exhaustion_threshold:return {'action':'EXIT_FULL' if p.unrealized_pnl_pct<0 else 'TAKE_PARTIAL','reason':'adverse momentum/event context','new_stop_loss':self._safer_stop(p,.5)}
        if p.unrealized_pnl_pct>0 and score>=self.config.momentum_extension_threshold:return {'action':'TRAIL_STOP','reason':'favorable momentum/event context','new_stop_loss':self._safer_stop(p,.75)}
        if p.unrealized_pnl_pct>0:return {'action':'MOVE_STOP_TO_BREAKEVEN','reason':'profitable position; protect capital','new_stop_loss':p.entry_price}
        return {'action':'HOLD','reason':'no bounded exit trigger','new_stop_loss':p.stop_loss}
    def decide_exit(self,p:Position,candles:list[Candle],events:list[MarketEvent],account_equity:float,daily_drawdown:float,total_drawdown:float)->dict:
        if len(candles)<self.config.atr_period+1:return {'action':'HOLD','reason':'insufficient data for exit context','new_stop_loss':p.stop_loss}
        m,e=self.analyze_momentum_context(p,candles),self.analyze_event_context(p,events); return self.dynamic_exit_policy(p,m,e,daily_drawdown,total_drawdown)|{'symbol':p.symbol,'momentum_score':round(m['score'],3),'event_score':round(e['score'],3),'event_risk':round(e['risk'],3)}

