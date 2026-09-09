import { api } from './client.js'

// US-AUTH-01/02/03 — admin login/logout (server sets/clears HttpOnly cookie).
export const login = ({ store_code, admin_username, password }) =>
  api.post('/auth/admin/login', { store_code, admin_username, password })

export const logout = () => api.post('/auth/admin/logout')

// US-AUTH-04 — one-time tablet setup for a table.
export const setupTable = ({ table_no, table_password }) =>
  api.post('/auth/tables', { table_no, table_password })
