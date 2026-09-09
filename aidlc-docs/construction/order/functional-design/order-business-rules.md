# Order — Business Rules (U4)

**단위**: U4 order | **스토리**: US-ORDER-05~12, US-SESSION-01~04
**PBT 대상 불변식**: BR-O15~O19 (Hypothesis). [PBT-03 total, PBT-06 상태/세션 상태기반]

---

## 주문 생성 / 채번
- **BR-O01**: `order_no`는 세션별 순차 = `max(session 내 order_no)+1`(첫 주문=1). UniqueConstraint(session_id, order_no)로 중복 방지; 충돌 시 재채번 후 재실패면 409.
- **BR-O02**: `items`는 서버 스냅샷 — 각 항목 `{menu_id, name, unit_price, qty}`이며 name·unit_price는 **서버가 MenuService로 재조회한 값**(클라이언트 입력 가격/명 무시). `total = Σ(unit_price × qty)`. [SEC-05]
- **BR-O03**: 주문 항목은 1개 이상(빈 장바구니 확정 거부, 422). 각 qty ≥ 1(정수).
- **BR-O04**: 주문의 모든 menu_id는 **자기 매장의 미삭제 메뉴**여야 한다. 삭제/타매장 메뉴 포함 시 거부(422/404, 존재 미노출). [SEC-08]
- **BR-O05**: 주문은 **활성 세션**에만 생성 가능(만료/종료 세션 → 401). 생성된 주문은 그 세션에 귀속(US-SESSION-01).
- **BR-O06**: 주문 생성/세션 종료는 단일 트랜잭션(원자적); 실패 시 롤백, SSE 발행은 commit 성공 후에만. [RES-10]

## 세션 종료 / 이력
- **BR-O07**: 세션 종료 시 세션의 미삭제 주문을 OrderHistory로 복사(items/total/status/created_at 보존 + session_closed_at 기록) 후 원본 소프트삭제, session.status=closed. 이후 현재 목록/총액=0.
- **BR-O08**: 이력 이동은 원본과 items·total·order_no를 **정확히 보존**한다(정산 신뢰성).
- **BR-O09**: 세션 종료는 관리자 권한, 자기 매장 세션만(타매장 404). [SEC-08]

## 상태 / 삭제
- **BR-O10**: 상태는 `pending`/`preparing`/`done` enum만 허용(그 외 422). 관리자는 유효 상태값으로 자유 설정 가능(정정 목적 역방향 허용).
- **BR-O11**: 주문 삭제는 소프트 삭제(deleted_at). 삭제 주문은 현재·이력 조회 및 총액 계산에서 제외. 자기 매장만(404). [SEC-08]
- **BR-O12**: 상태 변경·삭제·생성은 store 토픽과 해당 session 토픽 양쪽에 SSE 이벤트를 발행(관리자·고객 동시 반영, US-ORDER-08/11). 신규 주문은 2초 이내 관리자 화면 반영(NFR-P2).

## 조회 / 격리
- **BR-O13**: 고객 조회는 자기 세션 미삭제 주문만(이전 세션·이용완료 제외, US-ORDER-07). 관리자 조회는 매장 전체 + 선택적 table_id/status 필터(US-ORDER-12).
- **BR-O14**: 전 계층 store_id 격리 + 서비스 소유권 재확인(리포지토리 + 서비스 이중 방어). 오류는 일반화 + correlation_id. [SEC-08][SEC-15]

## 불변식 (PBT 대상)
- **BR-O15**: **총액 불변식** — 임의의 유효 (menu, qty) 항목 집합에 대해 생성된 주문의 `total == Σ(unit_price × qty)`이며, unit_price는 항상 서버 메뉴 단가와 일치한다. [PBT-03]
- **BR-O16**: **채번 단조성/유일성** — 한 세션에서 연속 생성된 주문의 order_no는 1부터 1씩 증가하며 세션 내에서 유일하다.
- **BR-O17**: **가격 변조 무효** — 클라이언트가 임의 가격을 보내더라도 저장된 unit_price·total은 서버 메뉴 단가 기준값과 동일하다(클라 입력 무시). [SEC-05]
- **BR-O18**: **이력 보존 왕복** — 세션 종료 후, 이동된 OrderHistory 집합의 (order_no, items, total)은 종료 직전 활성 주문 집합과 정확히 일치하고, 현재 활성 주문 조회 결과는 공집합·총액 0이다. [PBT-06]
- **BR-O19**: **삭제 총액 정합** — 임의의 주문 부분집합을 소프트삭제하면 테이블 총액은 남은(미삭제) 주문 total의 합과 같다.

---

## 스토리 ↔ 규칙 추적성
| 스토리 | 규칙 |
|--------|------|
| US-ORDER-05 주문 확정 | BR-O01~O06, O15~O17 |
| US-ORDER-06 실패 처리 | BR-O06 (롤백/장바구니 유지) |
| US-ORDER-07 세션 내역 | BR-O13 |
| US-ORDER-08 고객 SSE | BR-O12 |
| US-ORDER-09 관리자 모니터링 | BR-O12 (2s) |
| US-ORDER-10 상세 | BR-O02, O14 |
| US-ORDER-11 상태 변경 | BR-O10, O12 |
| US-ORDER-12 테이블 필터 | BR-O13 |
| US-SESSION-01 첫 주문 귀속 | BR-O05 |
| US-SESSION-02 주문 삭제 | BR-O11, O19 |
| US-SESSION-03 세션 종료→이력 | BR-O07~O09, O18 |
| US-SESSION-04 이력 조회 | BR-O08, O13, O14 |
