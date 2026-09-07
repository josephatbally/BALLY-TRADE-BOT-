import { apiRequest } from './client';

export type PositionType = 'BUY' | 'SELL' | 'UNKNOWN';

export interface OpenPosition {
  ticket: number;
  symbol: string;
  type: PositionType;
  volume: number;
  open_price: number;
  current_price: number;
  stop_loss: number;
  take_profit: number;
  profit: number;
  swap: number;
  magic: number;
  comment: string | null;
  open_time: string | null;
}

export interface PositionsResponse {
  status: string;
  connected: boolean;
  count: number;
  positions: OpenPosition[];
}

/**
 * Retrieve all currently open MT5 positions.
 *
 * This is read-only.
 */
export async function getOpenPositions(): Promise<PositionsResponse> {
  return apiRequest<PositionsResponse>('/api/v1/positions');
}