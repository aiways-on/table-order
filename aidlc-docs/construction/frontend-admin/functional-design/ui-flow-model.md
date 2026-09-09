# U6 frontend-admin — UI Flow & Logic Model

**Unit**: U6 frontend-admin (관리자 UI, React + Vite 정적앱)
**Consumes**: U2 auth (`/api/auth/*`, `access_token` HttpOnly 쿠키), U3 menu (`/api/menus/*`), U4 order (`/api/orders/*`, `/api/sessions/{id}/close`, `/api/history`, SSE `/api/orders/stream`).
**Design decisions (approved, recommended)**: Q1 react-router + Context/hooks · Q2 EventSource + 재연결 시 REST 재조회(RES-10) · Q3 Vite dev proxy + docker-compose 서비스(nginx, :5174).

## 1. Screens & Routes
| Route | Screen | Stories | Auth |
|---|---|---|---|
| `/login` | 매장 로그인 (store_code · admin_username · password) | US-AUTH-01/02/03 | public |
| `/` (redirect → `/dashboard`) | — | — | protected |
| `/dashboard` | 테이블 그리드 실시간 모니터링 + 주문 상세/상태변경/삭제/세션종료 | US-ORDER-09/10/11/12, US-SESSION-02/03 | protected |
| `/menus` | 메뉴 목록 + 등록/수정/삭제/순서조정 | US-MENU-04/05/06/07 | protected |
| `/tables` | 테이블 태블릿 초기 설정(table_no · table_password) | US-AUTH-04 | protected |
| `/history` | 종료된 세션의 과거 주문 이력 | US-SESSION-04 | protected |

## 2. Navigation & Layout
- `AppLayout`: 상단 네비(대시보드·메뉴·테이블설정·이력) + 로그아웃 버튼. `<Outlet/>`로 페이지 렌더.
- `ProtectedRoute`: 인증 미확정이면 로딩, 미인증이면 `/login` 리다이렉트.
- `LoginPage`는 레이아웃 밖.

## 3. State Management (Context + hooks)
- `AuthContext`: `{ auth: {store_id, role} | null, loading, login(), logout() }`.
  - 쿠키는 HttpOnly라 JS로 읽을 수 없음 → 부트 시 인증 상태를 **선택적 프로브**로 확인. 프로브 API가 없으므로 로그인 성공 시 `store_id`를 `localStorage("admin_store")`에 저장해 새로고침 후에도 로그인 UI를 유지(US-AUTH-02). 실제 권한은 서버 쿠키가 결정 — API가 401을 반환하면 상태를 비우고 `/login`으로 보냄(BR-FA03).
- 페이지-로컬 상태는 `useState`/`useEffect`. 전역 스토어 라이브러리 미도입(규모 과함).

## 4. API Integration Map
| UI action | API |
|---|---|
| 로그인 | `POST /api/auth/admin/login` `{store_code, admin_username, password}` → 쿠키 세팅, `{store_id, role}` |
| 로그아웃 | `POST /api/auth/admin/logout` (쿠키 삭제) |
| 테이블 설정 | `POST /api/auth/tables` `{table_no, table_password}` → `{table_id, table_no}` |
| 주문 목록(그리드) | `GET /api/orders/store?table_id=&status=` → `OrderOut[]` |
| 주문 상세 | `GET /api/orders/{id}` → `OrderOut`(items 포함) |
| 상태 변경 | `PATCH /api/orders/{id}/status` `{status: pending\|preparing\|done}` |
| 주문 삭제 | `DELETE /api/orders/{id}` → 204 |
| 세션 종료 | `POST /api/sessions/{session_id}/close` → 204 |
| 이력 조회 | `GET /api/history` → `HistoryOut[]` |
| 메뉴 목록 | `GET /api/menus/flat` → `MenuOut[]` (display_order 순) |
| 메뉴 등록/수정/삭제 | `POST /api/menus` · `PUT /api/menus/{id}` · `DELETE /api/menus/{id}` |
| 메뉴 순서 | `POST /api/menus/reorder` `{menu_ids: [...permutation]}` |

- 모든 요청은 `credentials: 'include'` (쿠키 동봉). 기본 base는 상대경로 `/api` (Vite proxy / nginx가 백엔드로 전달).

## 5. Realtime (SSE) — 대시보드
- `useOrderStream(onEvent)` 훅: `new EventSource('/api/orders/stream', { withCredentials: true })`.
- 백엔드는 이벤트명 없이 `data: {json}` 전송 → `es.onmessage`에서 `JSON.parse`, `type`으로 분기:
  - `order_created` → 해당 테이블 카드 하이라이트 + 목록 재조회.
  - `order_status` → 해당 주문 상태 갱신.
  - `order_deleted` → 목록에서 제거.
  - `session_closed` → 테이블 카드 비활성.
- **재연결(RES-10)**: `es.onerror` 시 EventSource 자동 재연결 + 지수백오프 상한. 재연결 성공/주기적으로 `GET /api/orders/store` **전체 재조회**로 정합화(누락 이벤트 복구). 15s keep-alive ping은 브라우저가 자동 처리.

## 6. Dashboard grid model (US-ORDER-09/12)
- store 주문 목록을 `table_id`로 그룹핑 → 테이블 카드 그리드. 각 카드: 테이블 라벨 + 활성 주문 수 + 최신 상태.
- 테이블 필터 드롭다운(US-ORDER-12) → `?table_id=` 재조회.
- 카드/주문 클릭 → 상세 패널(items·total·상태버튼 pending→preparing→done·삭제·세션종료).

## 7. Build/Deploy (Q3 A)
- **개발**: `npm run dev` (Vite :5174), `vite.config.js`가 `/api`를 `http://localhost:8000`으로 프록시(same-origin 쿠키 유지).
- **배포**: multi-stage Dockerfile(node build → nginx serve). `docker-compose.yml`에 `frontend-admin` 서비스(:5174) 추가, nginx가 `/api`를 backend로 리버스 프록시. 백엔드 CORS 오리진에 `http://localhost:5174` 포함(이미 문서화됨).
