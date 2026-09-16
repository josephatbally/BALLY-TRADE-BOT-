import {apiRequest} from './client';

export type OrderAction = 'BUY' | 'SELL';

export interface ExecuteOrderInput {
  symbol: string;
  action: OrderAction;
  lot_size?: number;
}

export interface ExecuteOrderResult {
  status?: string;
  order_sent?: boolean;
  reason?: string;
  ticket?: number;
  [key: string]: unknown;
}

export async function executeOrder(
  input: ExecuteOrderInput,
): Promise<ExecuteOrderResult> {
  return apiRequest<ExecuteOrderResult>('/api/v1/orders/execute', {
    method: 'POST',
    body: JSON.stringify({
      symbol: input.symbol.toUpperCase(),
      action: input.action,
      lot_size: input.lot_size,
    }),
  });
}

export interface CloseOrderResult {
  status?: string;
  closed?: boolean;
  closed_count?: number;
  reason?: string;
  [key: string]: unknown;
}

export async function closePosition(ticket: number): Promise<CloseOrderResult> {
  return apiRequest<CloseOrderResult>(`/api/v1/orders/close/${ticket}`, {
    method: 'POST',
  });
}

export async function closeAllPositions(): Promise<CloseOrderResult> {
  return apiRequest<CloseOrderResult>('/api/v1/orders/close-all', {
    method: 'POST',
  });
}
