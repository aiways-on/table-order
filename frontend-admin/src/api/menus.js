import { api } from './client.js'

// US-MENU-04~07 — admin menu management.
export const listMenus = () => api.get('/menus/flat') // MenuOut[] in display_order
export const createMenu = (payload) => api.post('/menus', payload)
export const updateMenu = (id, payload) => api.put(`/menus/${id}`, payload)
export const deleteMenu = (id) => api.del(`/menus/${id}`)
// BR-M14 / BR-FA12 — menu_ids must be the exact permutation of the store's menus.
export const reorderMenus = (menu_ids) => api.post('/menus/reorder', { menu_ids })
