"""Run from project root: python examples/sample_run.py"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from event_aware_liquidity_hunter import Candle, EventAwareLiquidityHunter, MarketEvent, Position

def make_candles():
    candles=[]
    for i in range(240):
        close=100+i*.12+(i%5-2)*.08
        candles.append(Candle(f'2026-08-08T{i:02d}:00:00Z',close-.18,close+.35,close-.4,close,900+i*3))
    last=candles[-1]; low=min(c.low for c in candles[-21:-1])-.5
    close=last.close-1.3
    candles[-1]=Candle(last.timestamp,close-.18,close+.35,low,close,last.volume*1.6)
    return candles

if __name__=='__main__':
    agent=EventAwareLiquidityHunter(); market=make_candles()
    print('ENTRY DECISION:',agent.decide_entry('BTC-USD',market,10_000,0,0,0),sep='\n')
    position=Position('BTC-USD','LONG',market[-1].close-.6,market[-1].close,1,market[-1].close-2,market[-1].close+4,.006,market[-4].timestamp)
    events=[MarketEvent('2026-08-08T12:00:00Z','statement','Constructive market statement','Synthetic sample',.55,.35,'demo',['BTC'])]
    print('\nEXIT DECISION:',agent.decide_exit(position,market,events,10_000,0,0),sep='\n')

