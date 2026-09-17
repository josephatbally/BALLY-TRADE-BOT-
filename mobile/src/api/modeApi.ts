import { apiRequest } from './client';

export type OperatingMode = 'Technical' | 'Hybrid';

export interface ModeStatusResponse {
  mode: string;
  is_hybrid: boolean;
  is_technical: boolean;
  status?: string;
}

export async function fetchTradingMode(): Promise<OperatingMode> {
  try {
    const data = await apiRequest<ModeStatusResponse>('/api/v1/mode');
    return data.mode?.toLowerCase() === 'hybrid' ? 'Hybrid' : 'Technical';
  } catch (error) {
    console.warn('[modeApi] Failed to fetch mode from backend:', error);
    return 'Technical';
  }
}

export async function updateTradingMode(mode: OperatingMode): Promise<boolean> {
  try {
    await apiRequest<ModeStatusResponse>('/api/v1/mode', {
      method: 'PUT',
      body: JSON.stringify({ mode: mode.toLowerCase() }),
    });
    return true;
  } catch (error) {
    console.warn('[modeApi] Failed to update mode on backend:', error);
    return false;
  }
}
