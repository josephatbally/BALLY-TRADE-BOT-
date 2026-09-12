import { apiRequest } from './client';

export interface AccountResponse {
  status: string;
  connected: boolean;
  balance: number;
  equity: number;
  profit: number;
  margin: number;
  free_margin: number;
  open_trades: number;
  currency: string;
}

export async function getAccountInfo(): Promise<AccountResponse> {
  return apiRequest<AccountResponse>('/api/v1/account');
}
