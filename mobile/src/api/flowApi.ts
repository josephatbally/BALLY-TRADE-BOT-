export type FlowCandle = {
  open: number;
  high: number;
  low: number;
  close: number;
  time?: string | number;
};

export type FlowFactor = {
  name: string;
  score: number;
  weight: string;
};

export type FlowValidationCheck = {
  name: string;
  status: 'PASS' | 'FAIL' | 'READY' | 'SIMULATION';
  detail: string;
};

export type SymbolFlowData = {
  status: string;
  symbol: string;
  timestamp: number;
  quote: {
    bid: number;
    ask: number;
    spread: number;
    change_pct: number;
  };
  bias: 'BULLISH' | 'BEARISH';
  candles: {
    M15: FlowCandle[];
    H1: FlowCandle[];
    H4: FlowCandle[];
  };
  confluence: {
    order_block: { detected: boolean; type: string; level: number };
    fair_value_gap: { detected: boolean; status: string; range: string };
    liquidity_sweep: { swept: boolean; side: string };
    session: string;
    volume_quality: string;
  };
  confidence: {
    score: number;
    factors: FlowFactor[];
  };
  decision: {
    action: 'BUY' | 'SELL' | 'HOLD';
    symbol: string;
    entry_price: number;
    stop_loss: number;
    take_profit_1: number;
    take_profit_2: number;
    risk_reward_ratio: string;
    status: string;
  };
  validation: {
    passed: boolean;
    checks: FlowValidationCheck[];
  };
};

export async function getSymbolFlow(symbol: string): Promise<SymbolFlowData> {
  const response = await fetch(`/api/v1/flow/${encodeURIComponent(symbol)}`);

  if (!response.ok) {
    throw new Error(`Flow request failed: ${response.status}`);
  }

  return response.json() as Promise<SymbolFlowData>;
}
