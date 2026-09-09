# U5 frontend-customer — UI Business Rules (BR-FC*)

프론트엔드(고객/태블릿) 계층 규칙. 백엔드 BR-O*/BR-A*를 UI에서 재현·소비하는 규칙만 다룬다. 서버가 권위이며 UI는 편의/표시 계층.

| ID | Rule | Source story | Enforcement |
|---|---|---|---|
| BR-FC01 | 모든 인증 요청은 세션 토큰을 `X-Session-Token` 헤더로 전송한다(쿠키 아님). SSE는 `?token=`. | US-AUTH-05 | `api/client.js` `setSessionToken` 주입 |
| BR-FC02 | 세션 토큰은 태블릿 localStorage(`customer_session`)에 저장 → 재방문/새로고침 시 자동 로그인(입장 화면 생략). | US-AUTH-05 | `SessionContext` 부트 로드 |
| BR-FC03 | 임의 API가 401(세션 만료/종료)을 반환하면 저장 세션을 즉시 폐기하고 `/start`로 유도한다. | US-AUTH-05 | `client.js` onUnauthorized → `SessionContext.clear()` |
| BR-FC04 | 세션 미확정 상태에서 `/menu`·`/orders` 직접 접근은 `/start`로 리다이렉트한다. | US-AUTH-05 | `SessionRoute` |
| BR-FC05 | 메뉴는 서버가 준 카테고리 그룹(`groups[]`) 순서·구성대로 표시한다. UI는 재정렬/필터 임의 변경 금지. | US-MENU-01/02 | `MenuPage` 그룹 렌더 |
| BR-FC06 | 메뉴 상세는 이미지 URL·설명·가격을 표시하되, **주문 시 서버가 재조회한 단가**가 최종이다. 장바구니 price는 표시용. | US-MENU-03, BR-O17 | 주문 payload는 `{menu_id, qty}`만 |
| BR-FC07 | 장바구니는 로컬 전용이다. 담기(중복 시 qty+1)·수량조절(0이면 제거)·비우기·총액(Σ price×qty) 실시간 갱신. 변경 시 localStorage(`customer_cart`) 반영으로 새로고침에도 유지. | US-ORDER-01/02/03/04 | `CartContext` |
| BR-FC08 | 주문 확정 실패(네트워크/4xx/5xx) 시 **장바구니를 유지**하고 오류 메시지를 표면화한다. 성공 시에만 장바구니를 비운다. | US-ORDER-05/06 | `MenuPage` submit 핸들러 |
| BR-FC09 | 주문 성공 시 서버가 부여한 `order_no`를 사용자에게 노출하고 주문내역 화면으로 이동한다. | US-ORDER-05 | 성공 토스트 + navigate `/orders` |
| BR-FC10 | 빈 장바구니로는 주문 버튼을 비활성화(제출 불가)한다. 서버도 422로 방어(BR-O). | US-ORDER-05 | 버튼 disabled |
| BR-FC11 | 주문내역 화면은 현재 세션의 주문만(GET /api/orders) 보여준다(자기 세션 격리, BR-O14). | US-ORDER-07 | `OrdersPage` |
| BR-FC12 | 주문 상태는 SSE로 실시간 반영한다. `order_created`/`order_status`/`order_deleted` 수신 시 내역을 재조회(정합화). | US-ORDER-08 | `useOrderStream` → refetch |
| BR-FC13 | `session_closed` 이벤트 수신 시 세션 종료를 안내하고 세션을 폐기 후 `/start`로 이동한다. | US-ORDER-08, BR-O05 | `useOrderStream` onEvent |
| BR-FC14 | SSE 연결 끊김 시 EventSource 자동 재연결에 의존하고, 재연결·주기적으로 REST 전체 재조회로 누락 이벤트를 보정한다(RES-10). | US-ORDER-08 | `OrdersPage` resync |
| BR-FC15 | 상태 코드→한글 라벨 매핑은 단일 소스(`STATUS_LABEL`)로 관리한다(received/preparing/done/served). | US-ORDER-07/08 | `api/orders.js` |

## Extension 준수 (U5 scope)
- **Security**: 토큰 헤더 전송(BR-FC01), 401 즉시 폐기(BR-FC03), 클라 가격 미신뢰(BR-FC06), 세션 격리(BR-FC11). SEC-05 입력검증은 서버 권위.
- **Resiliency**: SSE 재연결+REST 정합화(BR-FC14, RES-10), 주문 실패 시 장바구니 보존(BR-FC08).
- **PBT**: N/A — 백엔드 불변식(BR-O15~O19)에서 검증됨. 프론트는 컴포넌트/유닛 테스트(vitest).
