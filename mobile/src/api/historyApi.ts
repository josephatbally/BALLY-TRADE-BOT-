import { apiRequest } from './client';

export interface HistorySummaryResponse {
  status: string;
  connected: boolean;
  days: number;
  win_rate: number;
  total_trades: number;
  wins: number;
  losses: number;
  profit_factor: number;
  net_profit: number;
}

export interface HistoryDeal {
  ticket: number;
  order: number;
  position_id: number;
  symbol: string;
  type: number; // 0 = BUY, 1 = SELL
  entry: number; // 0 = IN, 1 = OUT
  volume: number;
  price: number;
  profit: number;
  swap: number;
  commission: number;
  fee: number;
  comment?: string | null;
  time?: string | null;
  time_msc?: number;
}

export interface HistoryDealsResponse {
  status: string;
  connected: boolean;
  days: number;
  symbol?: string | null;
  count: number;
  deals: HistoryDeal[];
}

export async function getHistorySummary(days: number = 7): Promise<HistorySummaryResponse> {
  return apiRequest<HistorySummaryResponse>(`/api/v1/history/summary?days=${days}`);
}

export async function getHistoryDeals(days: number = 30, symbol?: string): Promise<HistoryDealsResponse> {
  const query = symbol ? `?days=${days}&symbol=${encodeURIComponent(symbol)}` : `?days=${days}`;
  return apiRequest<HistoryDealsResponse>(`/api/v1/history${query}`);
}
