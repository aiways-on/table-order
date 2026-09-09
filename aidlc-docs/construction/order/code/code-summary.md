# Code Summary — U4 order

**단위**: U4 order (Order + 세션 라이프사이클 + 실시간 SSE)
**스토리**: US-ORDER-05~12, US-SESSION-01~04
**신규 DB 테이블 없음** — U1의 Order/TableSession/OrderHistory 재사용 → 마이그레이션 불필요.

---

## 생성 파일 (application code)

| 파일 | 책임 |
|------|------|
| `backend/app/order/__init__.py` | 패키지 마커 |
| `backend/app/order/schemas.py` | OrderItemIn(menu_id,qty≥1; extra=ignore로 클라 가격 무시), OrderCreate(items≥1), OrderItemOut, OrderOut, StatusUpdate(enum), HistoryOut |
| `backend/app/order/repository.py` | `OrderRepository(TenantScopedRepository[Order])` — max_order_no(삭제 포함), session_orders, store_orders(필터), get_session(store 격리), add_history, list_history |
| `backend/app/order/events.py` | store_topic/session_topic + 이벤트 페이로드 빌더(order_created/order_status/order_deleted/session_closed) |
| `backend/app/order/service.py` | `OrderService` — create(채번·MenuService 스냅샷·total·409 재시도), list_session, get(고객=자기세션/관리자=매장), list_store, update_status, delete(soft), close_session(→OrderHistory 복사+원본 soft-delete+세션 closed), list_history |
| `backend/app/order/sse.py` | `event_stream(topic)` async 제너레이터(keep-alive ping, metrics 연계, 구독 정리), SSE_HEADERS |
| `backend/app/order/router.py` | 주문 CRUD + status + delete + `/api/sessions/{id}/close` + `/api/history` + SSE 2종; 조회/쓰기 가드, db.commit 경계, U3 set_context(ctx) 재확립 패턴 |

**수정 파일**: `backend/app/main.py` — order 라우터 등록(이전 배선 확인, 변경 없음).

## 생성 파일 (tests)
| 파일 | 커버리지 |
|------|----------|
| `backend/tests/test_order_service.py` | 확정·빈장바구니·삭제/타매장 메뉴 거부·채번(삭제 후 미재사용)·상태 자유전이·세션종료→이력·교차테넌트 404·타세션 404 |
| `backend/tests/test_order_properties.py` | Hypothesis PBT: BR-O15 total, BR-O16 채번 단조/유일, BR-O17 가격변조 무효, BR-O18 이력 왕복, BR-O19 삭제 총액 정합 |
| `backend/tests/test_order_api.py` | 고객 확정/조회, 클라 가격 무시, 관리자 필터/상태/삭제, 세션종료→이력, 권한 401, SSE 연결 스모크(관리자/고객) |

## API 계약 (U5/U6 소비용)
- `POST /api/orders` (고객, X-Session-Token) → 201 OrderOut
- `GET /api/orders?limit&offset` (고객) → list[OrderOut] (자기 세션)
- `GET /api/orders/store?table_id&status` (관리자 쿠키) → list[OrderOut]
- `GET /api/orders/{id}` (관리자 | 고객[자기세션]) → OrderOut
- `PATCH /api/orders/{id}/status` (관리자) {status} → OrderOut
- `DELETE /api/orders/{id}` (관리자) → 204
- `POST /api/sessions/{id}/close` (관리자) → 204 (이력 이동)
- `GET /api/history?table_id&date_from&date_to` (관리자) → list[HistoryOut]
- SSE `GET /api/orders/stream` (관리자 쿠키) — topic `store:{store_id}`
- SSE `GET /api/orders/session/stream?token=` (고객) — topic `session:{session_id}`
- SSE 이벤트: `order_created` / `order_status` / `order_deleted` / `session_closed`

## 검증
- `pytest`: **82 passed** (기존 57 + U4 25). Hypothesis 속성 테스트 포함.
- SSE는 연결 스모크 수준 검증(전체 실시간 통합은 Build & Test 단계).

## 설계 준수 / 주의점
- **가격 스냅샷**(BR-O02/O17): 서버가 MenuService로 재조회한 단가·명만 저장. OrderItemIn `extra=ignore`로 클라 전송 가격은 스키마 단계에서 폐기.
- **채번 유일성**(BR-O01/O16): max_order_no가 소프트삭제 행 포함 계산 → 삭제된 order_no 재사용 방지. UniqueConstraint 경합 시 재시도 후 409.
- **원자성/발행 순서**(BR-O06/O12): 서비스는 flush만, 라우터가 commit → **commit 성공 후** event_bus.publish_sync(store+session 양 토픽).
- **격리**(BR-O14): 리포지토리 store_id 강제 + 서비스 소유권 재확인(교차테넌트/타세션 404).
- **컨텍스트 스레드 전파**: 동기 엔드포인트는 threadpool 워커별 contextvar 분리 → 각 엔드포인트가 set_context(ctx) 재확립(U3 패턴 동일).
- **단일 인스턴스 트레이드오프**: 고객 SSE는 스트림 수명 동안 요청 DB 세션 점유. 수평 확장 시 Redis pub/sub 전환(RES-08).
