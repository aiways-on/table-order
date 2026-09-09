# U5 frontend-customer — UI Flow & Logic Model

**Unit**: U5 frontend-customer (고객/태블릿 주문 UI, React + Vite 정적앱)
**Consumes**: U2 auth (`POST /api/auth/sessions` → `session_token`), U3 menu (`GET /api/menus` 카테고리 그룹), U4 order (`POST/GET /api/orders`, SSE `/api/orders/session/stream?token=`).
**핵심 차이(vs U6 admin)**: 고객 인증은 **HttpOnly 쿠키가 아니라 `X-Session-Token` 헤더** (SSE는 `?token=` 쿼리). 토큰은 태블릿 localStorage에 저장 → 자동 로그인(US-AUTH-05).
**Design decisions (U6와 정합)**: react-router + Context/hooks · EventSource + 재연결 시 REST 재조회(RES-10) · Vite dev proxy(:5173) + docker-compose(nginx).

## 1. Screens & Routes
| Route | Screen | Stories | Guard |
|---|---|---|---|
| `/start` | 태블릿 세션 시작(store_code · table_no · table_password). 저장된 세션 있으면 자동 통과 | US-AUTH-05 | public |
| `/` (redirect → `/menu`) | — | — | session |
| `/menu` | 카테고리별 메뉴 탐색 + 상세 + 장바구니(담기/수량/총액/비우기) + 주문 확정 | US-MENU-01/02/03, US-ORDER-01/02/03/04/05/06 | session |
| `/orders` | 현재 세션 주문 내역 + 실시간 상태(SSE) | US-ORDER-07/08 | session |

## 2. Navigation & Layout
- `AppLayout`: 상단바(매장명·테이블번호·"메뉴"/"주문내역" 탭). `<Outlet/>` 렌더.
- `SessionRoute`: 세션 미확정이면 로딩, 세션 없으면 `/start` 리다이렉트.
- `StartPage`는 레이아웃 밖.

## 3. State Management (Context + hooks)
- `SessionContext`: `{ session: {session_id, session_token, store_id, table_id} | null, loading, start(), clear() }`.
  - 부트 시 `localStorage("customer_session")` 로드 → 있으면 자동 로그인(US-AUTH-05). 토큰을 API 클라이언트에 주입(`setSessionToken`).
  - 임의 API가 401(세션 만료/종료)이면 세션 상태를 비우고 `/start`로 유도(BR-FC03).
- `CartContext`: 로컬 장바구니(`localStorage("customer_cart")`) — 새로고침에도 유지(US-ORDER-03). items·add·setQty·remove·clear·total.
- 페이지-로컬 상태는 `useState`/`useEffect`. 전역 스토어 라이브러리 미도입.

## 4. API Integration Map
| UI action | API |
|---|---|
| 세션 시작 | `POST /api/auth/sessions` `{store_code, table_no, table_password}` → `{session_id, session_token, store_id, table_id}` |
| 메뉴 목록 | `GET /api/menus` (X-Session-Token) → `{groups:[{category, items:[MenuOut]}]}` |
| 주문 확정 | `POST /api/orders` `{items:[{menu_id, qty}]}` (X-Session-Token) → `OrderOut`(order_no) |
| 세션 내역 | `GET /api/orders?limit&offset` (X-Session-Token) → `OrderOut[]` |

- 모든 요청은 세션 토큰을 `X-Session-Token` 헤더로 동봉(클라이언트가 주입). 기본 base는 상대경로 `/api`(Vite proxy / nginx).
- **가격은 서버 권위**: 주문 확정 시 `menu_id`·`qty`만 전송(단가·명은 서버 재조회, BR-O02/O17). 장바구니의 price·name은 화면 표시용.

## 5. Cart (local) — US-ORDER-01~04
- 담기: 동일 menu 이미 있으면 qty+1, 없으면 신규(qty=1).
- 수량 조절: `setQty(menu_id, n)`, n<1이면 항목 제거. 총액 = Σ(price×qty) 실시간.
- 비우기: 전체 삭제(확인).
- 지속성: 변경 시 localStorage 반영 → 새로고침 유지(US-ORDER-03).

## 6. 주문 확정 흐름 — US-ORDER-05/06
- "주문하기" → `POST /api/orders`. 성공 → 주문번호 토스트/화면 표시 → 장바구니 비우고 `/orders` 이동.
- 실패(네트워크/422/409 등) → **장바구니 유지**(비우지 않음) + 오류 메시지 표면화(BR-FC08).

## 7. Realtime (SSE) — 주문 내역 US-ORDER-08
- `useOrderStream(token, onEvent)` 훅: `new EventSource('/api/orders/session/stream?token='+token)`.
- 백엔드는 이벤트명 없이 `data: {json}` → `onmessage`에서 `JSON.parse`, `type` 분기:
  - `order_created`/`order_status`/`order_deleted` → 세션 내역 재조회 또는 상태 갱신.
  - `session_closed` → 세션 종료 안내 → 세션 clear → `/start`.
- **재연결(RES-10)**: `onerror` 시 EventSource 자동 재연결 + 재연결/주기적으로 `GET /api/orders` 전체 재조회로 정합화. 15s keep-alive는 브라우저 처리.

## 8. Build/Deploy
- **개발**: `npm run dev`(Vite :5173), `vite.config.js`가 `/api`를 `http://localhost:8000`으로 프록시(SSE 포함).
- **배포**: multi-stage Dockerfile(node build → nginx serve). docker-compose에 `frontend-customer`(:5173) 추가, nginx가 `/api` 리버스 프록시. 백엔드 CORS 오리진에 `http://localhost:5173` 포함 필요.
