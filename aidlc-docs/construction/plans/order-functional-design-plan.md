# Functional Design 계획 — U4 order (Part 1: Planning / Questions)

**단계**: CONSTRUCTION → Functional Design
**단위**: U4 order (Order + 세션 라이프사이클 + 실시간 SSE)
**구현 스토리**: US-ORDER-05~12 (주문 확정/내역/SSE/상태변경/필터), US-SESSION-01~04 (첫 주문 세션 귀속/주문 삭제/세션 종료→이력/이력 조회).
> US-ORDER-01~04(장바구니 담기·수량·로컬유지·비우기)는 **클라이언트(localStorage)** 책임 → U5 frontend-customer. 서버는 "주문 확정 시에만" 관여(US-ORDER-03).

**승계 컨텍스트**: U1 `app/shared/models`(Order, TableSession, OrderHistory — 이미 정의), `app/core/events`(event_bus: topic pub/sub, SSE 백엔드), `app/core`(context, errors, database, logging), `app/shared/repository`(TenantScopedRepository); U2 `app/auth/dependencies`(require_admin/require_customer, verify_session), U3 `app/menu/service`(단가·명 스냅샷 조회).

> Order/TableSession/OrderHistory ORM 엔티티는 U1에 존재 → **신규 테이블/마이그레이션 없음**.

---

## 확인 질문 (A/B/C 중 택1, 필요 시 X)

### Q1. 주문번호(order_no) 채번
- **A.** 세션별 순차 — `max(session 내 order_no)+1` (세션당 1,2,3…). U1 UniqueConstraint(session_id, order_no)와 정합. 동시성은 트랜잭션+유니크 제약으로 방어(충돌 시 재시도/409)
- **B.** 매장 전역 순차
- **C.** UUID/랜덤

[Answer]: A

### Q2. 주문 항목 스냅샷 & 가격 신뢰
- **A.** 서버가 각 menu_id를 **U3 MenuService로 재조회**하여 name·단가를 확정하고 items(JSON: menu_id/name/qty/unit_price) 스냅샷 저장, total=Σ(unit_price×qty) 서버 계산. **클라이언트가 보낸 가격은 무시**(가격 변조 방지). 삭제/타매장 메뉴 포함 시 거부 [SEC-05][SEC-08]
- **B.** 클라이언트가 보낸 가격/명을 신뢰
- **C.** menu_id만 저장(스냅샷 없음, 조인 조회)

[Answer]: A

### Q3. 실시간(SSE) 채널 구성
- **A.** 토픽 2종 — 관리자용 `store:{store_id}`(전 테이블 모니터링), 고객용 `session:{session_id}`(자기 세션). 주문 생성/상태변경/삭제 시 두 토픽에 발행. 관리자 SSE는 JWT 쿠키(require_admin) 인증, 고객 SSE는 EventSource 제약상 `?token=` 쿼리의 세션 토큰으로 인증. keep-alive/재연결 시 최신 상태 재조회 [RES-10]
- **B.** 단일 매장 토픽만(고객도 매장 토픽 구독, 클라이언트 필터)
- **C.** SSE 미사용(폴링)

[Answer]: A

### Q4. 상태 전이 규칙 (US-ORDER-11)
- **A.** 상태값은 `pending`/`preparing`/`done` enum으로 검증. 관리자는 유효 상태값으로 자유 설정(정정 목적 역방향 허용). 변경 시 저장 + SSE 발행
- **B.** 순방향 전이만 강제(pending→preparing→done, 되돌리기 금지)
- **C.** 상태 없음(완료 토글만)

[Answer]: A

### Q5. 세션 종료 → 이력 이동 (US-SESSION-03)
- **A.** 종료 시 트랜잭션 내에서 세션의 활성 주문을 **OrderHistory로 복사**(items/total/status/created_at 보존 + session_closed_at 기록) 후 원본 주문을 소프트삭제, 세션 status=closed. 이후 현재 주문 목록·총액은 0으로 리셋. 종료는 관리자 권한(자기 매장). U2 close_session을 확장/대체
- **B.** 이력 이동 없이 세션만 closed(주문은 그대로 남김)
- **C.** 하드 삭제(이력 미보존)

[Answer]: A

### Q6. 주문 삭제 (US-SESSION-02)
- **A.** 소프트 삭제(deleted_at) — 현재/이력 조회에서 제외, 테이블 총액 재계산, 관리자·고객 SSE 발행. 자기 매장 주문만(IDOR 404) [SEC-08]
- **B.** 하드 삭제
- **C.** 취소 상태로 표시(별도 status)

[Answer]: A

### Q7. 권한 경계
- **A.** 고객(require_customer): 자기 세션 주문 확정·자기 세션 주문 내역 조회·자기 세션 SSE 구독. 관리자(require_admin): 매장 전체 주문 조회/테이블 필터·상세·상태변경·삭제·세션 종료·과거 이력 조회·매장 SSE 구독. 전 계층 store_id 격리 + 서비스 소유권 재확인
- **B.** 고객도 매장 전체 주문 조회 가능
- **C.** 모두 관리자 인증 필요

[Answer]: A

---

## 산출 예정 문서 (승인 후 생성)
- `aidlc-docs/construction/order/functional-design/order-logic-model.md` — 주문 생성(채번·스냅샷·total), 내역 조회(현재 세션/관리자 필터), 상태 변경, 삭제, 세션 종료→이력, SSE 발행/구독 흐름, U1/U2/U3 계약 배선, 동시성/오류 처리
- `aidlc-docs/construction/order/functional-design/order-business-rules.md` — BR-O01~ (채번·total 불변식·스냅샷·상태·격리·이력 보존; PBT 대상 불변식 포함: total=Σ단가×수량[PBT-03], 상태/세션 상태기반[PBT-06])

---

**질문에 답해주시면 audit.md에 기록하고, 모호함이 없으면 Part 2(설계 문서 생성)로 진행합니다.**
