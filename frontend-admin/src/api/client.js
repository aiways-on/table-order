// Thin fetch wrapper. All requests send the HttpOnly session cookie
// (credentials: 'include'). Non-2xx responses raise ApiError so callers can
// surface the message; 401 triggers the global "session expired" handler.
// [BR-FA03][BR-FA15]

const BASE = '/api'

export class ApiError extends Error {
  constructor(status, message, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

// Registered by AuthContext so any 401 clears auth state and routes to /login.
let onUnauthorized = null
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

async function request(method, path, body) {
  const opts = {
    method,
    credentials: 'include',
    headers: {},
  }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(`${BASE}${path}`, opts)
  } catch (networkErr) {
    throw new ApiError(0, '서버에 연결할 수 없습니다. 잠시 후 다시 시도하세요.', null)
  }

  if (res.status === 401) {
    if (onUnauthorized) onUnauthorized()
    throw new ApiError(401, '세션이 만료되었습니다. 다시 로그인하세요.', null)
  }

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const detail =
      (data && (data.detail || data.message)) || `요청 실패 (${res.status})`
    throw new ApiError(res.status, typeof detail === 'string' ? detail : JSON.stringify(detail), data)
  }
  return data
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  put: (path, body) => request('PUT', path, body),
  patch: (path, body) => request('PATCH', path, body),
  del: (path) => request('DELETE', path),
}
