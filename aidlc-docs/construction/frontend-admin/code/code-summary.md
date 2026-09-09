# U6 frontend-admin — Code Generation Summary

**Unit**: U6 frontend-admin (React + Vite 관리자 UI, 정적앱)
**Stages executed**: Functional Design (EXECUTE) + Code Generation (EXECUTE). NFR Requirements / NFR Design / Infrastructure Design SKIPPED (cross-cutting NFRs, patterns & shared infra fixed in U1; SEC/RES-10 applied as UI rules).
**Consumes**: U2 auth (`/api/auth/*`, `access_token` HttpOnly cookie), U3 menu (`/api/menus/*`), U4 order (`/api/orders/*`, `/api/sessions/{id}/close`, `/api/history`, SSE `/api/orders/stream`).
**Verification**: `npm test` → **11 passed** (client 6 · order helpers 2 · LoginPage 3). `npm run build` → success (dist, gzip ~59KB JS).

## Files (frontend-admin/)
| File | Purpose |
|---|---|
| `package.json` | React 18 + react-router-dom 6 + Vite 5; vitest + testing-library (dev) |
| `vite.config.js` | dev proxy `/api → :8000` (same-origin cookie); vitest jsdom config |
| `index.html`, `src/main.jsx`, `src/index.css` | app shell + styling |
| `src/App.jsx` | routes; `/login` public, rest behind `ProtectedRoute` + `AppLayout` |
| `src/api/client.js` | fetch wrapper — `credentials:'include'`, `ApiError`, global 401 handler (BR-FA03/15) |
| `src/api/auth.js` / `menus.js` / `orders.js` | typed API calls + status helpers/labels |
| `src/auth/AuthContext.jsx` | login/logout, store_id in localStorage (BR-FA02), 401 → clear |
| `src/hooks/useOrderStream.js` | EventSource `/api/orders/stream` + resync-on-(re)connect (RES-10, BR-FA10) |
| `src/components/ProtectedRoute.jsx`, `AppLayout.jsx` | auth gate + nav shell |
| `src/pages/LoginPage.jsx` | US-AUTH-01/02/03 (BR-FA01/04) |
| `src/pages/DashboardPage.jsx` | US-ORDER-09/10/11/12 + US-SESSION-02/03; grid by table_id, SSE, detail/status/delete/close |
| `src/pages/MenusPage.jsx` | US-MENU-04/05/06/07; CRUD + up/down reorder → `/menus/reorder` permutation |
| `src/pages/TablesPage.jsx` | US-AUTH-04 tablet setup |
| `src/pages/HistoryPage.jsx` | US-SESSION-04 read-only history |
| `Dockerfile`, `nginx.conf`, `.dockerignore` | multi-stage build → nginx serve + `/api` reverse-proxy (SSE-friendly) |
| `README.md`, `.gitignore` | docs + ignores |
| `src/api/client.test.js`, `src/api/orders.test.js`, `src/pages/LoginPage.test.jsx`, `src/test/setup.js` | vitest suite (11) |

## Root changes
- `docker-compose.yml`: added `frontend-admin` service (build ./frontend-admin, `5174:80`, depends_on backend). Backend CORS already lists `http://localhost:5174`.

## Stories delivered
US-AUTH-01/02/03/04, US-MENU-04/05/06/07, US-ORDER-09/10/11/12, US-SESSION-02/03/04.

## Extension compliance
- **Security Baseline** — session via HttpOnly cookie (no token in JS); all requests `credentials:'include'`; 401 → clear+redirect; client validation mirrors server SEC-05 (menu/login/table); rate-limit (429) messages surfaced verbatim, no client bypass (SEC-14). **Compliant.**
- **Resiliency Baseline (RES-10)** — SSE auto-reconnect + full REST resync on (re)connect to heal missed events; non-2xx surfaced (no silent failure); network errors wrapped in friendly ApiError. **Compliant** for single-instance target.
- **PBT** — N/A for this UI unit (PBT-02 assigned to U5 frontend-customer; admin extensions are RES-10/SEC). Logic helpers covered by unit tests instead.

## Notes / tradeoffs
- Order/History rows expose `table_id` (UUID) not a human table number — backend `OrderOut` carries no `table_no`. UI shows a short id; a future backend enhancement could join table_no.
- Auth state is client-optimistic (localStorage store_id); server cookie is authoritative — any 401 reconciles by clearing and redirecting to `/login`.
