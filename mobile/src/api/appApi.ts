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