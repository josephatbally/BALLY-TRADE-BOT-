import { apiRequest } from './client';

export interface BrokerIdentity {
  company: string;
  server: string;
  login: number | null;
  leverage: number | null;
  name: string | null;
  trade_mode: string;
}

export interface AccountResponse {
  status: string;
  connected: boolean;
  broker?: BrokerIdentity;
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

export const getAccount = getAccountInfo;
export const getAccountData = getAccountInfo;