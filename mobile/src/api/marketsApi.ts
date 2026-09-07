import {apiRequest} from './client';

/**
 * BALLY FLOW market API contract.
 *
 * The mobile application is a consumer of the authoritative
 * backend trading engine. No trading intelligence is implemented here.
 */

export type TradingMode = 'technical' | 'hybrid';

export type TradingDecision =
  | 'BUY'
  | 'SELL'
  | 'NO_TRADE';

export type MarketDirection =
  | 'BULLISH'
  | 'BEARISH'
  | 'NEUTRAL'
  | 'NONE';

export type MarketSymbol =
  | 'XAUUSD'
  | 'EURUSD'
  | 'GBPUSD'
  | 'USDJPY'
  | 'XAGUSD'
  | 'NASDAQ';

export const SUPPORTED_MARKETS: MarketSymbol[] = [
  'XAUUSD',
  'EURUSD',
  'GBPUSD',
  'USDJPY',
  'XAGUSD',
  'NASDAQ',
];

export const ANALYSIS_TIMEFRAMES = [
  'H4',
  'H1',
  'M15',
] as const;

export type AnalysisTimeframe =
  (typeof ANALYSIS_TIMEFRAMES)[number];

/**
 * ============================================================
 * MARKET DATA
 * ============================================================
 */

export interface Candle {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LatestCandle {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketTimeframeData {
  status?: string;
  timeframe: string;
  requested_candle_count?: number;
  candle_count?: number;
  candles?: Candle[];
  latest_closed_candle?: LatestCandle | null;
  latest_candle_time?: number | string | null;
  latest_closed_candle_time?: number | string | null;
  error?: string | null;
}

/**
 * ============================================================
 * SCANNER
 * ============================================================
 */

export interface MarketScanItem {
  status?: string;
  scanner?: string;
  market?: string;
  broker_symbol?: string | null;
  symbol?: string | null;

  analysis_order?: string[];
  top_down?: boolean;
  market_data_only?: boolean;

  timeframe_count?: number;
  ready_timeframe_count?: number;
  data_ready?: boolean;

  readiness?: unknown;
  timeframes?: Record<string, MarketTimeframeData>;

  technical_analysis?: unknown;
  fundamental_analysis?: unknown;
  hybrid_analysis?: unknown;

  decision?: unknown;
  errors?: string[];

  [key: string]: unknown;
}

export interface MarketsResponse {
  status: string;
  count: number;
  markets: string[];
}

export interface ScannerStatusResponse {
  status?: string;
  scanner?: string;
  markets?: string[];
  market_count?: number;
  timeframes?: string[];
  timeframe_count?: number;
  expected_stream_count?: number;
  default_candle_count?: number;
  market_data_only?: boolean;

  technical_analysis?: boolean;
  fundamental_analysis?: boolean;
  hybrid_analysis?: boolean;
  trading_decision?: boolean;
  risk_management?: boolean;
  position_sizing?: boolean;
  execution?: boolean;

  [key: string]: unknown;
}

/**
 * ============================================================
 * SINGLE-MARKET APPLICATION PIPELINE
 * ============================================================
 *
 * Backend:
 *
 * POST /api/v1/markets/{symbol}/scan
 *
 * The response comes directly from BallyFlowApplication
 * and contains the scanner result plus the authoritative
 * analysis / decision / trade-plan / execution layers.
 */

export interface MarketPipelineResponse {
  status: string;
  application: string;
  version: string;
  mode: TradingMode;
  market: string;

  scan: MarketScanItem | Record<string, unknown>;

  analysis?: unknown;
  technical_analysis?: unknown;

  decision?: TradingDecision | string | null;
  signal?: TradingDecision | string | null;
  reason?: string | null;

  trade_plan?: unknown;
  execution?: unknown;

  [key: string]: unknown;
}

/**
 * ============================================================
 * ALL-MARKET SCAN
 * ============================================================
 *
 * Backend:
 *
 * POST /api/v1/markets/scan
 */

export interface ScanAllMarketsPayload {
  status: string;
  application: string;
  version: string;
  mode: TradingMode;

  scan: {
    status?: string;
    scanner?: string;
    top_down?: boolean;
    market_data_only?: boolean;
    analysis_order?: string[];
    markets?: MarketScanItem[];
    market_count?: number;
    expected_market_count?: number;
    timeframes_per_market?: number;
    expected_stream_count?: number;
    ready_market_count?: number;
    partial_market_count?: number;
    failed_market_count?: number;
    ready_timeframe_count?: number;
    required_timeframe_count?: number;
    data_ready?: boolean;
    ready_markets?: string[];
    partial_markets?: string[];
    failed_markets?: string[];
    decision?: unknown;
    [key: string]: unknown;
  };

  decisions?: unknown;

  [key: string]: unknown;
}

/**
 * ============================================================
 * MARKET ANALYSIS
 * ============================================================
 */

export interface AnalysisDecision {
  signal?: TradingDecision | string | null;
  decision?: TradingDecision | string | null;
  confidence?: number | null;
  dominant_direction?: MarketDirection | string | null;
  reason?: string | null;
  reasons?: string[];

  [key: string]: unknown;
}

export interface AIConfidence {
  confidence?: number | null;
  score?: number | null;
  technical_score?: number | null;
  market_conditions_score?: number | null;
  threshold?: number | null;

  [key: string]: unknown;
}

/**
 * Authoritative analysis object produced by the backend.
 *
 * The backend engine owns the actual structure, so this type
 * intentionally preserves additional fields instead of
 * attempting to recreate trading-engine logic in React Native.
 */
export interface MarketAnalysisItem {
  market?: string;
  symbol?: string;
  broker_symbol?: string | null;

  status?: string;
  analysis_ready?: boolean;

  decision?:
    | TradingDecision
    | string
    | AnalysisDecision
    | null;

  signal?: TradingDecision | string | null;

  confidence?: number | null;
  dominant_direction?:
    | MarketDirection
    | string
    | null;

  reason?: string | null;
  reasons?: string[];

  technical_analysis?: unknown;
  ai_confidence?:
    | AIConfidence
    | number
    | null;

  market_conditions?: unknown;
  confluence?: unknown;
  pipeline_status?: unknown;

  [key: string]: unknown;
}

export interface SingleMarketAnalysisResponse {
  status: string;
  mode: TradingMode;
  market: string;
  analysis: MarketAnalysisItem;

  [key: string]: unknown;
}

export interface AllMarketAnalysisResponse {
  status: string;
  mode: TradingMode;
  market_count: number;
  markets: string[];

  analysis: Record<
    string,
    MarketAnalysisItem
  >;

  execution?: {
    allowed?: boolean;
    order_send_allowed?: boolean;
    [key: string]: unknown;
  };

  [key: string]: unknown;
}

/**
 * ============================================================
 * API FUNCTIONS
 * ============================================================
 */

/**
 * Return the six agreed BALLY FLOW markets.
 */
export function getMarkets(): Promise<MarketsResponse> {
  return apiRequest<MarketsResponse>(
    '/api/v1/markets',
  );
}

/**
 * Return scanner capabilities/status.
 */
export function getScannerStatus(): Promise<ScannerStatusResponse> {
  return apiRequest<ScannerStatusResponse>(
    '/api/v1/markets/scanner',
  );
}

/**
 * Run one market through the complete backend
 * BALLY FLOW application pipeline.
 */
export function scanMarket(
  symbol: MarketSymbol | string,
  count?: number,
): Promise<MarketPipelineResponse> {
  const query =
    typeof count === 'number'
      ? `?count=${encodeURIComponent(count)}`
      : '';

  return apiRequest<MarketPipelineResponse>(
    `/api/v1/markets/${encodeURIComponent(
      symbol.toUpperCase(),
    )}/scan${query}`,
    {
      method: 'POST',
    },
  );
}

/**
 * Run the complete six-market market-data scan.
 */
export function scanAllMarkets(
  count?: number,
): Promise<ScanAllMarketsPayload> {
  const query =
    typeof count === 'number'
      ? `?count=${encodeURIComponent(count)}`
      : '';

  return apiRequest<ScanAllMarketsPayload>(
    `/api/v1/markets/scan${query}`,
    {
      method: 'POST',
    },
  );
}

/**
 * Run authoritative analysis for all six markets.
 *
 * Backend:
 * GET /api/v1/markets/analysis?mode=technical|hybrid
 */
export function getMarketAnalysis(
  mode?: TradingMode,
): Promise<AllMarketAnalysisResponse> {
  const query = mode
    ? `?mode=${encodeURIComponent(mode)}`
    : '';

  return apiRequest<AllMarketAnalysisResponse>(
    `/api/v1/markets/analysis${query}`,
  );
}

/**
 * Run authoritative analysis for one market.
 *
 * Backend:
 * GET /api/v1/markets/{symbol}/analysis?mode=technical|hybrid
 */
export function getSingleMarketAnalysis(
  symbol: MarketSymbol | string,
  mode?: TradingMode,
): Promise<SingleMarketAnalysisResponse> {
  const query = mode
    ? `?mode=${encodeURIComponent(mode)}`
    : '';

  return apiRequest<SingleMarketAnalysisResponse>(
    `/api/v1/markets/${encodeURIComponent(
      symbol.toUpperCase(),
    )}/analysis${query}`,
  );
}

