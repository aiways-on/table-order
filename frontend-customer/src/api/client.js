// Thin fetch wrapper for the customer app. Unlike the admin app (HttpOnly
// cookie), the customer authenticates with an X-Session-Token header, which
// SessionContext injects via setSessionToken. Non-2xx responses raise ApiError
// so callers can surface the message; 401 triggers the global handler that
// clears the stored session and routes back to /start. [BR-FC01][BR-FC03]

const BASE = '/api'

export class ApiError extends Error {
  constructor(status, message, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

// The active session token, injected by SessionContext (null when logged out).
let sessionToken = null
export function setSessionToken(token) {
  sessionToken = token || null
}

// Registered by SessionContext so any 401 clears session state → /start.
let onUnauthorized = null
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

async function request(method, path, body) {
  const opts = { method, headers: {} }
  if (sessionToken) opts.headers['X-Session-Token'] = sessionToken
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(`${BASE}${path}`, opts)
  } catch {
    throw new ApiError(0, '서버에 연결할 수 없습니다. 잠시 후 다시 시도하세요.', null)
  }

  if (res.status === 401) {
    if (onUnauthorized) onUnauthorized()
    throw new ApiError(401, '세션이 만료되었습니다. 다시 입장해 주세요.', null)
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
    // Backend shape is {error:{status,message,correlation_id}}; fall back
    // gracefully for other shapes.
    const detail =
      (data && (data.error?.message || data.detail || data.message)) ||
      `요청 실패 (${res.status})`
    throw new ApiError(res.status, typeof detail === 'string' ? detail : JSON.stringify(detail), data)
  }
  return data
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  patch: (path, body) => request('PATCH', path, body),
  del: (path) => request('DELETE', path),
}
