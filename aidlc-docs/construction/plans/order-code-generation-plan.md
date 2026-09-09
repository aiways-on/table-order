# Code Generation 계획 — U4 order (Part 1: Planning)

**단계**: CONSTRUCTION → Code Generation
**단위**: U4 order (Order + 세션 라이프사이클 + 실시간 SSE)
**코드 위치**: `backend/app/order/` (앱 코드), 문서 `aidlc-docs/construction/order/code/`
**이 계획이 Code Generation의 단일 진실 원천입니다.**

---

## 단위 컨텍스트
**구현 스토리**: US-ORDER-05(확정), 06(실패), 07(세션내역), 08(고객 SSE), 09(관리자 SSE), 10(상세), 11(상태변경), 12(테이블 필터); US-SESSION-01(첫 주문 귀속), 02(주문 삭제), 03(세션 종료→이력), 04(이력 조회).

**의존성(승계)**: U1 `app/shared`(models Order/TableSession/OrderHistory, TenantScopedRepository), `app/core`(events.event_bus, context, errors, database, logging, metrics); U2 `app/auth`(require_admin/require_customer, AuthService.verify_session); U3 `app/menu/service.MenuService`(단가·명). **하위 소비자**: U5/U6 프론트.

**소유 로직**: 주문 서비스/리포지토리/스키마/SSE/라우터. **신규 DB 테이블 없음** → 마이그레이션 불필요.

**제공 계약**:
- `POST /api/orders`(고객 확정), `GET /api/orders`(세션 내역), `GET /api/orders/store`(관리자 필터), `GET /api/orders/{id}`(상세), `PATCH /api/orders/{id}/status`, `DELETE /api/orders/{id}`
- `POST /api/sessions/{id}/close`(이력 이동 종료), `GET /api/history`(과거 이력)
- SSE: `GET /api/orders/stream`(관리자·쿠키), `GET /api/orders/session/stream?token=`(고객)

---

## 실행 단계 (Numbered Steps)

### Step 1: 모듈 구조
- [x] `app/order/__init__.py`
- 경로: `backend/app/order/`

### Step 2: 스키마 (검증 SEC-05) — BR-O02/O03
- [x] `app/order/schemas.py` (OrderItemIn{menu_id, qty≥1}, OrderCreate{items min 1}, OrderItemOut, OrderOut, StatusUpdate{status enum}, StoreOrderQuery 필터, HistoryOut)
- 경로: `backend/app/order/`

### Step 3: 리포지토리
- [x] `app/order/repository.py` (`OrderRepository(TenantScopedRepository[Order])` — session 내역/매장 필터/max order_no/history insert·조회 헬퍼)
- 경로: `backend/app/order/`

### Step 4: 이벤트 헬퍼
- [x] `app/order/events.py` (store_topic/session_topic, 이벤트 페이로드 builder: order_created/order_status/order_deleted/session_closed)
- 경로: `backend/app/order/`

### Step 5: 서비스 (Business Logic) — BR-O01~O19
- [x] `app/order/service.py` (`OrderService`: create[채번·MenuService 스냅샷·total·원자성·409 재시도], list_session, list_store, get, update_status, delete[soft], close_session[→OrderHistory], list_history; commit 후 event_bus 발행)
- 경로: `backend/app/order/`

### Step 6: SSE + API 라우터
- [x] `app/order/sse.py` (event-stream 응답 생성기, keep-alive, metrics 연계, 구독 정리)
- [x] `app/order/router.py` (주문 CRUD + status + delete + sessions/{id}/close + history + SSE 2종; 조회/쓰기 가드, db.commit 경계, set_context(ctx) 재확립 [U3 패턴])
- [x] `app/main.py`에 order 라우터 등록 (기존 파일 수정)
- 경로: `backend/app/order/`, `backend/app/main.py`

### Step 7: 단위 + 속성 테스트 (PBT)
- [x] `tests/test_order_service.py` (확정·빈장바구니 거부·삭제/타매장 메뉴 거부·채번·상태변경·삭제·세션종료→이력·이력조회·교차테넌트 404)
- [x] `tests/test_order_properties.py` (Hypothesis: BR-O15 total=Σ단가×수량, BR-O16 채번 단조/유일, BR-O17 가격변조 무효, BR-O18 이력 왕복, BR-O19 삭제 총액 정합) [PBT-03/06]
- [x] `tests/test_order_api.py` (고객 확정·세션 내역, 관리자 필터/상세/상태변경/삭제/세션종료/이력, 권한 401/403, SSE 연결 스모크)
- 경로: `backend/tests/`

### Step 8: 문서
- [x] `aidlc-docs/construction/order/code/code-summary.md`
- 경로: `aidlc-docs/construction/order/code/`

---

## 스토리 추적성
| 스토리 | 구현 위치 | 상태 |
|--------|-----------|:---:|
| US-ORDER-05 확정 | service.create, schemas.OrderCreate | [x] |
| US-ORDER-06 실패 처리 | service.create(트랜잭션 롤백) | [x] |
| US-ORDER-07 세션 내역 | service.list_session, router GET | [x] |
| US-ORDER-08 고객 SSE | sse.py, events.session_topic | [x] |
| US-ORDER-09 관리자 SSE | sse.py, events.store_topic | [x] |
| US-ORDER-10 상세 | schemas.OrderOut, router GET/{id} | [x] |
| US-ORDER-11 상태 변경 | service.update_status + 발행 | [x] |
| US-ORDER-12 테이블 필터 | service.list_store(필터) | [x] |
| US-SESSION-01 첫 주문 귀속 | service.create(활성 세션) | [x] |
| US-SESSION-02 주문 삭제 | service.delete(soft) + 발행 | [x] |
| US-SESSION-03 세션 종료→이력 | service.close_session | [x] |
| US-SESSION-04 이력 조회 | service.list_history | [x] |

---

## 범위 요약
- **총 8단계**. 신규 DB 테이블 없음(U1 Order/TableSession/OrderHistory 재사용) → 마이그레이션 불필요.
- 배포 아티팩트 변경 없음(기존 compose/backend 이미지에 포함).
- 테스트는 생성만, 실행은 Build & Test. 생성 후 로컬 pytest로 검증 예정. SSE는 연결 스모크 수준(전체 실시간 통합은 Build & Test).

---

**Part 2 완료** — 전체 스위트 82 통과(U4 신규 25: 서비스 8 + 속성 5[Hypothesis] + API 12). throwaway venv(py3.13, bcrypt 4.0.1) 검증 후 제거. 고객 SSE 엔드포인트 `Depends(get_db)` 수정 적용.
