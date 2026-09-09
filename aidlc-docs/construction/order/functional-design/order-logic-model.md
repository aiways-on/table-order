# Order — Functional Logic Model (U4)

**단위**: U4 order (Order + 세션 라이프사이클 + 실시간 SSE)
**스토리**: US-ORDER-05~12, US-SESSION-01~04
**결정(모두 A)**: 세션별 순차 채번 · 서버 가격 재조회 스냅샷 · SSE 2토픽(store/session) · enum 자유 상태전이 · 세션종료→OrderHistory 복사+소프트삭제 · 주문 소프트삭제 · 고객=자기세션/관리자=매장전체.

> Order/TableSession/OrderHistory 엔티티는 U1에 존재 → **신규 테이블/마이그레이션 없음**.

---

## 1. 승계 계약 배선

| 필요 | 출처 | 사용처 |
|------|------|--------|
| `Order`/`TableSession`/`OrderHistory` 모델 | U1 `app/shared/models` | 리포지토리 |
| `TenantScopedRepository` (store_id 강제 + deleted_at 필터) | U1 `app/shared/repository` | `OrderRepository` |
| `event_bus` (topic pub/sub, per-conn asyncio.Queue) | U1 `app/core/events` | SSE 발행/구독 |
| `require_admin` / `require_customer` / `verify_session` | U2 `app/auth` | 라우터 가드 / SSE 토큰 인증 |
| `MenuService.get` (단가·명) | U3 `app/menu/service` | 주문 항목 스냅샷 |
| `metrics.sse_connected/disconnected` | U1 `app/core/metrics` | SSE 관측 |

---

## 2. 컴포넌트 구조 (신규, `app/order/`)

```
app/order/
  __init__.py
  schemas.py       # OrderItemIn, OrderCreate, OrderItemOut, OrderOut, StatusUpdate, TableOrdersOut, HistoryOut
  repository.py    # OrderRepository(TenantScopedRepository[Order]) + history helpers
  service.py       # OrderService: create/list_session/list_store/get/update_status/delete/close_session/list_history
  events.py        # 토픽 헬퍼: store_topic(store_id), session_topic(session_id), 이벤트 페이로드 builder
  sse.py           # SSE 응답 생성기(EventSourceResponse 유사; keep-alive)
  router.py        # /api/orders + /api/orders/stream(admin) + /api/orders/session/stream(customer) + /api/sessions/{id}/close + /api/history
```

---

## 3. 로직 흐름

### 3.1 주문 확정 — US-ORDER-05/06, US-SESSION-01
```
POST /api/orders  (require_customer)
  body: OrderCreate { items: [{menu_id, qty}] }   # 가격/명은 받지 않음
  1. 빈 항목 → 422 (US-ORDER-05 빈 장바구니 거부)
  2. ctx.session_id로 활성 세션 확인(만료/종료 → 401)  # 세션은 U2 로그인 시 시작됨(US-SESSION-01: 첫 주문이 이 세션에 귀속)
  3. 각 menu_id를 MenuService.get(store 격리) → 없거나 타매장/삭제 → 422/404
  4. items 스냅샷 = [{menu_id, name, unit_price(server), qty}], total = Σ(unit_price×qty)  [BR-O02]
  5. order_no = max(session 내 order_no)+1  [BR-O01]
  6. Order insert (트랜잭션). UniqueConstraint(session_id, order_no) 충돌 시 1회 재채번/재시도 → 그래도 실패 시 409
  7. commit 후 event_bus.publish(store_topic, {type:"order_created", order}) + publish(session_topic, ...)
  8. 201 OrderOut (order_no 포함)
  실패 시: 트랜잭션 롤백, 일반화 오류(장바구니는 클라 유지) [SEC-15][RES-10]
```

### 3.2 현재 세션 주문 내역 — US-ORDER-07
```
GET /api/orders?limit&offset  (require_customer)
  → OrderRepository: store_id + session_id(ctx) + deleted_at IS NULL, created_at ASC
  → 현재 세션 주문만(이전 세션·이용완료 제외), 페이지네이션
  → 각 주문 order_no/시각/items/total/status
```

### 3.3 관리자 주문 조회/필터 — US-ORDER-09/10/12
```
GET /api/orders/store?table_id=&status=  (require_admin)
  → store_id 격리, 선택적 table_id/status 필터, 최신순
  → 테이블별 그룹/총액 계산 가능한 평면 목록 반환(그룹핑은 프론트)
GET /api/orders/{id}  (require_admin | require_customer[자기세션])  → 상세(items 전체)
```

### 3.4 상태 변경 — US-ORDER-08/11
```
PATCH /api/orders/{id}/status  (require_admin)
  body: { status: pending|preparing|done }
  → repo.get_or_404(id)  # 타매장 404 (SEC-08)
  → enum 검증, order.status = status, flush+commit
  → publish(store_topic,{type:"order_status",id,status}) + publish(session_topic(order.session_id),...)
  → 고객 SSE(US-ORDER-08)·관리자 SSE 즉시 반영, 2초 이내(NFR-P2)
```

### 3.5 주문 삭제 — US-SESSION-02
```
DELETE /api/orders/{id}  (require_admin)
  → repo.get_or_404 → soft_delete(deleted_at)
  → 테이블 총액 재계산은 조회 시 파생(별도 필드 없음)
  → publish(store_topic,{type:"order_deleted",id,table_id}) + session_topic
  → 204
```

### 3.6 세션 종료 → 이력 — US-SESSION-03
```
POST /api/sessions/{session_id}/close  (require_admin)
  트랜잭션:
    1. session = get(session_id) & store 소유 확인(타매장 404)  [SEC-08]
    2. 세션의 미삭제 활성 주문마다 OrderHistory insert
         (store_id/table_id/session_id/original_order_id/order_no/items/total/status/created_at/session_closed_at=now)
    3. 원본 주문 소프트삭제(deleted_at)
    4. session.status=closed, closed_at=now
  commit 후 publish(store_topic,{type:"session_closed",session_id,table_id})
  → 현재 주문 목록/총액 0 리셋 [BR-O07]
```
> **U2 close_session 관계**: U2는 세션 status만 닫았음. U4가 이력 이동을 포함한 **완전한 종료**를 제공. 라우터는 U4 버전을 정식 사용(관리자용). 고객측 U2 `/api/auth/sessions/close`는 이력 이동 없는 단순 종료로 유지(고객이 직접 종료하는 경우는 드묾; 정식 종료는 관리자).

### 3.7 과거 이력 조회 — US-SESSION-04
```
GET /api/history?table_id=&date_from=&date_to=  (require_admin)
  → OrderHistory: store_id 격리, 선택 필터, moved_at/created_at 역순
  → 주문번호/시각/items/total/session_closed_at
```

### 3.8 SSE 구독 — US-ORDER-08/09
```
GET /api/orders/stream            (require_admin, 쿠키)      → subscribe(store_topic(store_id))
GET /api/orders/session/stream?token=SESSION_TOKEN (고객)   → verify_session(token) → subscribe(session_topic(session_id))
  - text/event-stream, 각 이벤트 `data: {json}\n\n`
  - 주기적 keep-alive(`: ping`) 전송, 클라 끊기면 generator finally에서 큐 정리
  - 재연결 시 클라가 최신 목록 재조회(REST) → 상태 복구 [RES-10]
  - metrics.sse_connected/disconnected 관측
```
> 고객 SSE가 `?token=` 쿼리를 쓰는 이유: 브라우저 `EventSource`는 커스텀 헤더를 못 붙임. 토큰은 로그·URL 노출 최소화를 위해 TLS 전제(prod HTTPS)에서만 안전 — 로컬 HTTP 허용(SEC-04) 문서화.

---

## 4. 권한 · 격리
| 동작 | 고객 | 관리자 |
|------|:---:|:---:|
| 주문 확정 | ✅(자기 세션) | — |
| 현재 세션 내역 | ✅(자기 세션) | — |
| 매장 전체/필터 조회 | — | ✅ |
| 주문 상세 | ✅(자기 세션 주문) | ✅ |
| 상태 변경 | — | ✅ |
| 주문 삭제 | — | ✅ |
| 세션 종료(이력) | — | ✅ |
| 과거 이력 | — | ✅ |
| SSE | session 토픽 | store 토픽 |

모든 접근 store_id 격리 + 서비스 계층 소유권 재확인(IDOR 404).

---

## 5. 동시성 / 오류
- **채번 경합**: 트랜잭션 + UniqueConstraint(session_id, order_no); 충돌 시 1회 재채번, 재실패 409(클라 재시도).
- **주문 실패 원자성**: 생성/종료는 단일 트랜잭션, 실패 시 롤백(부분 반영 없음) [RES-10]. SSE 발행은 **commit 성공 후**에만.
- **일반화 오류** + correlation_id(SEC-15). 장바구니는 클라 유지(US-ORDER-06).

---

## 6. 하위 소비자
- **U5 frontend-customer**: 주문 확정, 세션 내역, 고객 SSE.
- **U6 frontend-admin**: 모니터링 그리드(store SSE), 상세, 상태변경, 삭제, 세션 종료, 이력.
