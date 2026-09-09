# Code Summary — U5 frontend-customer

**단위**: U5 frontend-customer (고객/태블릿 주문 UI, React 18 + Vite)
**스토리**: US-AUTH-05, US-MENU-01/02/03, US-ORDER-01~08
**소비**: U2 `POST /api/auth/sessions`, U3 `GET /api/menus`, U4 `POST/GET /api/orders` + SSE `GET /api/orders/session/stream?token=`.
**핵심 차이(vs U6 admin)**: 고객 인증은 `X-Session-Token` 헤더(쿠키 아님), SSE는 `?token=` 쿼리. 토큰은 localStorage 저장 → 자동 로그인.

---

## 생성 파일 (application code — `frontend-customer/`)

| 파일 | 책임 |
|------|------|
| `package.json` / `vite.config.js` / `index.html` | Vite 스캐폴딩. dev 서버 **:5173**, `/api`→`:8000` 프록시(SSE 포함) |
| `src/main.jsx` | BrowserRouter → SessionProvider → CartProvider → App |
| `src/api/client.js` | fetch 래퍼. `setSessionToken`으로 **X-Session-Token** 주입, 401 전역 핸들러, **백엔드 `{error:{message}}` 파싱**(admin의 잠재 버그 수정) |
| `src/api/auth.js` | `startSession` (POST /auth/sessions) |
| `src/api/menus.js` | `getMenusGrouped` → `groups[]` |
| `src/api/orders.js` | `createOrder`(menu_id·qty만 전송, BR-FC06), `listMyOrders`, `STATUS_LABEL`(pending/preparing/done) |
| `src/session/SessionContext.jsx` | 세션 상태 + localStorage 자동로그인(US-AUTH-05), 401→clear→/start(BR-FC03) |
| `src/cart/CartContext.jsx` | 로컬 장바구니 add/setQty/remove/clear/total/count + localStorage 지속(US-ORDER-01~04) |
| `src/hooks/useOrderStream.js` | EventSource `?token=` 구독, type 분기, 재연결 시 onResync(RES-10) |
| `src/components/SessionRoute.jsx` / `AppLayout.jsx` | 세션 가드(BR-FC04) + 상단바/탭 레이아웃 |
| `src/App.jsx` | 라우팅 `/start`·`/menu`·`/orders` |
| `src/pages/StartPage.jsx` | 테이블 입장 폼 + 자동로그인 리다이렉트 |
| `src/pages/MenuPage.jsx` | 카테고리 메뉴·상세 모달·장바구니 패널·주문 확정(성공만 clear, 실패 유지 BR-FC08) |
| `src/pages/OrdersPage.jsx` | 세션 주문내역 + SSE 실시간, session_closed→clear→/start(BR-FC13) |
| `src/index.css` | 모바일/태블릿 대응 스타일 |
| `Dockerfile` / `nginx.conf` / `README.md` | multi-stage(node→nginx), `/api` 리버스 프록시(버퍼링 off, SSE 타임아웃) |

**수정 파일**: `docker-compose.yml` — `frontend-customer` 서비스(**5173:80**) 추가. 백엔드 CORS는 이미 `localhost:5173` 허용(변경 불필요).

## 생성 파일 (tests — vitest/jsdom)
| 파일 | 커버리지 |
|------|----------|
| `src/api/client.test.js` | X-Session-Token 주입/생략, 204, 401 핸들러, `{error:{message}}` 파싱, 네트워크 오류 (7) |
| `src/api/orders.test.js` | 상태 라벨, createOrder가 menu_id·qty만 전송(가격 변조 방지) (3) |
| `src/cart/cart.test.jsx` | 담기/중복증가/총액/0→제거/비우기/localStorage 지속 (5) |
| `src/session/session.test.jsx` | 자동로그인 하이드레이션, start 지속, clear (3) |

## 검증
- `npm test`: **18 passed** (4 files)
- `npm run build`: OK (dist, 46 modules)

## 설계 준수 / 주의점
- **인증 헤더**(BR-FC01): 관리자 쿠키와 달리 세션 토큰 헤더 전송. SSE는 EventSource 제약상 `?token=`.
- **가격 서버 권위**(BR-FC06/BR-O17): 주문 payload는 `{menu_id, qty}`만. 장바구니 price/name은 표시 전용.
- **주문 실패 시 장바구니 보존**(BR-FC08): 성공에서만 `cart.clear()`.
- **실시간 정합**(BR-FC12/14, RES-10): SSE 이벤트→REST 전체 재조회, 재연결 시 onResync.
- **세션 종료**(BR-FC13): `session_closed` 수신 시 세션 폐기 후 `/start`.
- **client 오류 파싱**: U6 admin은 `data.detail||data.message`만 읽어 백엔드 `{error:{message}}`를 놓치는 잠재 버그가 있었음 — U5는 `data.error?.message` 우선 파싱으로 수정.
- **PBT**: N/A(백엔드 불변식에서 커버). 프론트는 컴포넌트/유닛 테스트.
