import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  API_BASE_URL,
  API_TIMEOUT_MS,
} from './config';

export class ApiError extends Error {
  public readonly status?: number;

  constructor(
    message: string,
    status?: number,
  ) {
    super(message);

    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Generic BALLY FLOW HTTP request client.
 * Phase 2: Automatically injects JWT Bearer token from AsyncStorage into every request.
 */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, API_TIMEOUT_MS);

  try {
    // Phase 2: Retrieve authenticated JWT token
    let authToken = '';
    try {
      authToken = (await AsyncStorage.getItem('@bally_auth_token')) || '';
      if (!authToken) {
        const storedUser = await AsyncStorage.getItem('@bally_auth_user');
        if (storedUser) {
          const parsed = JSON.parse(storedUser);
          authToken = parsed.token || '';
        }
      }
    } catch {
      // Non-blocking if storage is unavailable
    }

    const authHeaders: Record<string, string> = {};
    if (authToken) {
      authHeaders['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,

        headers: {
          Accept: 'application/json',
          ...authHeaders,

          ...(options.body
            ? {
                'Content-Type':
                  'application/json',
              }
            : {}),

          ...options.headers,
        },

        signal: controller.signal,
      },
    );

    const text = await response.text();

    let data: unknown = null;

    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        throw new ApiError(
          'The backend returned an invalid JSON response.',
          response.status,
        );
      }
    }

    if (!response.ok) {
      let message =
        `Request failed with status ${response.status}`;

      if (
        data &&
        typeof data === 'object' &&
        'detail' in data
      ) {
        const detail = (
          data as {
            detail?: unknown;
          }
        ).detail;

        if (typeof detail === 'string') {
          message = detail;
        }
      }

      throw new ApiError(
        message,
        response.status,
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (
      error instanceof Error &&
      error.name === 'AbortError'
    ) {
      throw new ApiError(
        'The request timed out. Please check the backend connection.',
      );
    }

    if (error instanceof Error) {
      throw new ApiError(
        `Unable to connect to BALLY FLOW backend: ${error.message}`,
      );
    }

    throw new ApiError(
      'An unexpected network error occurred.',
    );
  } finally {
    clearTimeout(timeoutId);
  }
}
