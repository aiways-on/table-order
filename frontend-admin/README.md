# frontend-admin (U6) — 테이블오더 관리자 UI

React + Vite 정적 앱. 매장 관리자가 로그인 → 실시간 주문 모니터링 → 상태 변경/삭제 →
테이블/세션 관리 → 메뉴 관리 → 주문 이력을 수행합니다.

## 개발 실행
```bash
npm install
npm run dev          # http://localhost:5174  (Vite proxy: /api → http://localhost:8000)
```
백엔드(U1~U4)를 `docker compose up` 또는 uvicorn으로 `:8000`에 먼저 띄워야 합니다.
백엔드 오리진을 바꾸려면: `VITE_BACKEND_ORIGIN=http://host:port npm run dev`.

## 테스트
```bash
npm test             # vitest (client / order helpers / LoginPage)
```

## 빌드 / 배포
```bash
npm run build        # dist/
```
또는 루트 `docker-compose.yml`의 `frontend-admin` 서비스 사용 (nginx가 `/api`를 backend로 프록시, :5174 노출).

## 인증 모델
- 세션은 백엔드가 발급하는 **HttpOnly 쿠키**(`access_token`, 16h). JS에서 읽을 수 없음.
- 로그인 성공 시 `store_id`만 localStorage에 저장해 새로고침 후 로그인 UI 유지(US-AUTH-02).
- 임의 API가 401을 반환하면 클라이언트 상태를 비우고 `/login`으로 이동.

## API 계약
`aidlc-docs/construction/frontend-admin/functional-design/ui-flow-model.md` 참조.
