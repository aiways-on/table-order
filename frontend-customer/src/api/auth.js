import { api } from './client.js'

// US-AUTH-05: start a table session. Returns
// { session_id, session_token, store_id, table_id }.
export function startSession({ storeCode, tableNo, tablePassword }) {
  return api.post('/auth/sessions', {
    store_code: storeCode,
    table_no: Number(tableNo),
    table_password: tablePassword,
  })
}
