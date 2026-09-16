from pathlib import Path

target = Path("mobile/src/api/ordersApi.ts")
content = target.read_text(encoding="utf-8")

extra_api = """
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
"""

if "closePosition" not in content:
    content = content.strip() + "\n" + extra_api
    target.write_text(content, encoding="utf-8")
    print("SUCCESS: mobile/src/api/ordersApi.ts updated with close methods!")
else:
    print("closePosition already present in ordersApi.ts.")
