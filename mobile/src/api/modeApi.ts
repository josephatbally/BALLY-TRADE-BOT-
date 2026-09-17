import { API_BASE_URL, getAuthHeaders } from './config';

export type OperatingMode = 'Technical' | 'Hybrid';

export interface ModeStatusResponse {
  mode: string;
  is_hybrid: boolean;
  is_technical: boolean;
  status?: string;
}

export async function fetchTradingMode(): Promise<OperatingMode> {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/mode`, {
      method: 'GET',
      headers,
    });
    if (!response.ok) {
      return 'Technical';
    }
    const data: ModeStatusResponse = await response.json();
    return data.mode?.toLowerCase() === 'hybrid' ? 'Hybrid' : 'Technical';
  } catch (error) {
    console.warn('[modeApi] Failed to fetch mode from backend:', error);
    return 'Technical';
  }
}

export async function updateTradingMode(mode: OperatingMode): Promise<boolean> {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/mode`, {
      method: 'PUT',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ mode: mode.toLowerCase() }),
    });
    return response.ok;
  } catch (error) {
    console.warn('[modeApi] Failed to update mode on backend:', error);
    return false;
  }
}
