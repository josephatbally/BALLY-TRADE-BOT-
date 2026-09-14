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

export async function getHistorySummary(days: number = 7): Promise<HistorySummaryResponse> {
  return apiRequest<HistorySummaryResponse>(`/api/v1/history/summary?days=${days}`);
}