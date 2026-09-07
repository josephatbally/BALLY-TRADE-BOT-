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
 *
 * Responsibilities:
 *
 * - Build API URLs
 * - Handle timeouts
 * - Handle network errors
 * - Parse JSON responses
 * - Convert API failures into ApiError
 *
 * Screens should use appApi.ts or marketsApi.ts
 * instead of calling fetch() directly.
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
    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,

        headers: {
          Accept: 'application/json',

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