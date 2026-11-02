const API_BASE = import.meta.env.VITE_API_URL ?? '';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  anonymousId?: string | null;
  signal?: AbortSignal;
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };

  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.anonymousId) headers['X-Anonymous-Session'] = options.anonymousId;

  const requestInit: RequestInit = {
    method: options.method ?? (options.body !== undefined ? 'POST' : 'GET'),
    headers,
  };
  if (options.body !== undefined) requestInit.body = JSON.stringify(options.body);
  if (options.signal !== undefined) requestInit.signal = options.signal;

  const response = await fetch(`${API_BASE}${path}`, requestInit);

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = undefined;
    }
    const message =
      typeof details === 'object' &&
      details !== null &&
      'detail' in details &&
      typeof (details as { detail: unknown }).detail === 'string'
        ? (details as { detail: string }).detail
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, details);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
