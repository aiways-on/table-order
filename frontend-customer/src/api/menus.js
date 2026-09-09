import { api } from './client.js'

// US-MENU-01/02: category-grouped menu for the customer screen.
// Backend returns { groups: [{ category, items: [MenuOut] }] }. [BR-FC05]
export async function getMenusGrouped() {
  const data = await api.get('/menus')
  return data?.groups ?? []
}
