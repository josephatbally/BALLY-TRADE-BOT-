import {apiRequest} from './client';

/**
 * ============================================================
 * HEALTH
 * ============================================================
 */

export type HealthResponse = {
  status: string;
  application: string;
  version: string;
  service: string;
};

/**
 * ============================================================
 * APPLICATION STATUS
 * ============================================================
 */

export type ScannerInfo = {
  name: string;
  status: string;

  markets: string[];

  market_count: number;

  timeframes: string[];

  timeframes_per_market: number;

  analysis_order: string[];

  top_down_hierarchy: string;

  stream_count: number;

  default_candle_count: number;

  technical_analysis: boolean;

  fundamental_analysis: boolean;

  hybrid_analysis: boolean;

  trading_decision: boolean;

  risk_management: boolean;

  position_sizing: boolean;

  execution: boolean;
};

export type ApplicationStatusResponse = {
  status: string;

  application: string;

  version: string;

  running: boolean;

  mode: TradingMode;

  technical_enabled: boolean;

  hybrid_enabled: boolean;

  scanner: ScannerInfo;
};

/**
 * ============================================================
 * TRADING MODE
 * ============================================================
 */

export type TradingMode =
  | 'technical'
  | 'hybrid';

export type ApplicationModeResponse = {
  mode: TradingMode;

  technical_enabled: boolean;

  hybrid_enabled: boolean;
};

export type UpdateModeResponse = {
  status: string;

  mode: TradingMode;

  technical_enabled: boolean;

  hybrid_enabled: boolean;
};

/**
 * ============================================================
 * API FUNCTIONS
 * ============================================================
 */

/**
 * Check whether the BALLY FLOW FastAPI service is reachable.
 */
export function getHealth() {
  return apiRequest<HealthResponse>(
    '/health',
  );
}

/**
 * Get the complete BALLY FLOW application status.
 *
 * This also provides the authoritative backend trading mode,
 * so DashboardScreen does not need a separate mode request.
 */
export function getApplicationStatus() {
  return apiRequest<ApplicationStatusResponse>(
    '/api/v1/app/status',
  );
}

/**
 * Get the current backend trading mode.
 *
 * Kept available for other screens that may need a dedicated
 * mode request.
 */
export function getApplicationMode() {
  return apiRequest<ApplicationModeResponse>(
    '/api/v1/app/mode',
  );
}

/**
 * Update the backend trading mode.
 */
export function updateApplicationMode(
  mode: TradingMode,
) {
  return apiRequest<UpdateModeResponse>(
    '/api/v1/app/mode',
    {
      method: 'PUT',

      body: JSON.stringify({
        mode,
      }),
    },
  );
}

/**
 * ============================================================
 * ACCOUNT INFO (MT5 PORTFOLIO)
 * ============================================================
 */

export type AccountInfoResponse = {
  status: string;
  connected: boolean;
  balance: number | null;
  equity: number | null;
  profit: number | null;
  margin: number | null;
  free_margin: number | null;
  open_trades: number | null;
  currency: string | null;
};

export function getAccountInfo() {
  return apiRequest<AccountInfoResponse>('/api/v1/account');
}

/**
 * ============================================================
 * AUTO TRADING
 * ============================================================
 */

export type AutoTradeResponse = {
  status?: string;
  auto_trading_enabled: boolean;
};

export function getAutoTradeStatus() {
  return apiRequest<AutoTradeResponse>('/api/v1/app/auto-trade');
}

export function setAutoTradeStatus(enabled: boolean) {
  return apiRequest<AutoTradeResponse>('/api/v1/app/auto-trade', {
    method: 'POST',
    body: JSON.stringify({
      enabled,
    }),
  });
}

export function startApplication() {
  return apiRequest<ApplicationStatusResponse>('/api/v1/app/start', {
    method: 'POST',
  });
}

export function stopApplication() {
  return apiRequest<ApplicationStatusResponse>('/api/v1/app/stop', {
    method: 'POST',
  });
}

export type BotLogEntry = {
  timestamp: string;
  level: string;
  message: string;
  details?: Record<string, any>;
};

export type BotTelemetryResponse = {
  enabled: boolean;
  running: boolean;
  mt5_connected: boolean;
  scan_interval: number;
  min_confidence: number;
  max_positions: number;
  current_positions_count: number;
  risk_pct: number;
  default_lot: number;
  last_scan_time: string | null;
  balance: number;
  equity: number;
  recent_logs: BotLogEntry[];
  last_analysis_summary?: Record<string, any>;
};

export function getBotTelemetry() {
  return apiRequest<BotTelemetryResponse>('/api/v1/app/bot/telemetry');
}

export function toggleBotAutoTrade(enabled: boolean) {
  return apiRequest<{status: string; auto_trading_enabled: boolean}>('/api/v1/app/bot/toggle', {
    method: 'POST',
    body: JSON.stringify({enabled}),
  });
}
