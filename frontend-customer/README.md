# frontend-customer (U5)

테이블오더 **고객/태블릿** 주문 UI. React 18 + Vite + react-router.

## 개발
```bash
npm install
npm run dev      # http://localhost:5173 (/api → http://localhost:8000 프록시)
npm test         # vitest
npm run build
```

## 인증 모델 (vs admin)
- 고객은 **`X-Session-Token` 헤더**로 인증한다(관리자의 HttpOnly 쿠키가 아님).
- 세션 토큰은 태블릿 localStorage(`customer_session`)에 저장 → 재방문 시 자동 로그인(US-AUTH-05).
- SSE(`GET /api/orders/session/stream?token=`)는 헤더를 못 실으므로 `?token=` 쿼리 사용.

## 화면
- `/start` — 매장코드·테이블번호·비밀번호로 세션 시작(저장된 세션 있으면 자동 통과)
- `/menu` — 카테고리별 메뉴 + 상세 + 로컬 장바구니(담기/수량/총액/비우기) + 주문 확정
- `/orders` — 현재 세션 주문 내역 + 실시간 상태(SSE)

## 소비 API
`POST /api/auth/sessions`, `GET /api/menus`, `POST /api/orders`, `GET /api/orders`,
SSE `GET /api/orders/session/stream?token=`.

## 배포
멀티스테이지 Dockerfile(node build → nginx). nginx가 `/api`를 backend로 리버스 프록시.
백엔드 CORS 허용 오리진에 `http://localhost:5173` 포함 필요.
