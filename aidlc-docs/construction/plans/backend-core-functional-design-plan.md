# Functional Design 계획 — U1 backend-core

**단계**: CONSTRUCTION → Functional Design (Part 1: Planning)
**단위**: U1 backend-core (횡단 기반: Tenant·Platform + 공용 도메인 모델)
**입력**: `unit-of-work.md`, `unit-of-work-story-map.md`(US-TENANT-01~05), `application-design.md`
**성격**: 기술 중립 비즈니스 로직/도메인 모델 설계 (인프라 관심사 제외)

이 문서는 (1) Functional Design 실행 체크리스트와 (2) 설계 결정 질문을 담고 있습니다.
`[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 산출물을 생성합니다.

---

## A. 실행 체크리스트 (승인/답변 후 수행)

- [x] `domain-entities.md` — 공용 도메인 엔티티(Store, Menu, Table, TableSession, Order, OrderHistory) 필드·관계·식별자·제약
- [x] `business-logic-model.md` — 테넌트 스코프·인가·검증·로깅·오류·헬스·백업 로직 모델
- [x] `business-rules.md` — 횡단 비즈니스 규칙(격리 불변식, 검증 규칙, 오류 표준, 로깅 마스킹, 헬스/백업 정책)
- [x] 확장 규칙(SEC/RES/PBT) 반영 및 불변식 명시
- [x] 스토리 US-TENANT-01~05 커버리지 확인
- [x] (프론트 없음 — frontend-components.md 미해당)

---

## B. 설계 초안 (질문 답변 후 확정)

**공용 엔티티(모든 엔티티 store_id 스코프)** — 필드는 답변에 따라 확정:
- **Store**(매장/테넌트): id, store_code, name, admin_username, admin_password_hash(bcrypt), created_at
- **Menu**: id, store_id, name, price, description, category, image_url, display_order, created_at
- **Table**: id, store_id, table_no, table_password_hash, created_at
- **TableSession**: id, store_id, table_id, status(active/closed), session_token, started_at, closed_at
- **Order**: id, store_id, table_id, session_id, order_no, items(JSON: name/qty/unit_price), total, status(pending/preparing/done), created_at
- **OrderHistory**: (Order와 동형) + moved_at/session_closed_at

---

## C. 질문 (Functional Design Questions)

## Question 1: 데이터베이스 엔진 확정
관계형 DB 엔진을 무엇으로 확정할까요? (요구사항 Q4=관계형)

A) PostgreSQL — JSON 타입·인덱스·동시성 우수, docker 이미지 표준 (권장)

B) MySQL/MariaDB

C) SQLite (초경량 demo, 동시성 제약)

X) Other

[Answer]: A

## Question 2: 기본 키(ID) 전략
엔티티 식별자를 어떻게 할까요?

A) UUID(문자열) — 테넌트 간 추측 어려움, IDOR 완화에 유리 `[SEC-08]` (권장)

B) 자동증가 정수 — 단순하나 순차 추측 가능

C) 정수 PK + 외부 노출용 별도 공개 식별자

X) Other

[Answer]: A

## Question 3: 삭제 방식(주문·메뉴)
삭제를 어떻게 처리할까요?

A) 소프트 삭제(deleted_at) — 감사/복구 유리, 총액 계산 시 제외 `[SEC-13]` (권장)

B) 하드 삭제 — 단순, 이력은 OrderHistory로만 보존

C) 혼합 — 주문=소프트, 메뉴=하드

X) Other

[Answer]: A

## Question 4: 주문번호(order_no) 형식
고객/관리자에게 보이는 주문번호를 어떻게 생성할까요?

A) 세션 내 순번(예: 테이블 세션당 1,2,3…) + 내부 UUID 분리 (사람이 읽기 쉬움, 권장)

B) 전역 순번

C) 날짜+랜덤 코드(예: 20260908-AB12)

X) Other

[Answer]: A

## Question 5: 시간/타임존 처리
타임스탬프를 어떻게 저장·표시할까요?

A) DB는 UTC 저장, 표시(프론트)에서 로컬 변환 (권장)

B) 매장 로컬 타임존 저장

X) Other

[Answer]: A

## Question 6: 테넌트 스코프 강제 지점
store_id 격리를 어디서 강제할까요?

A) Repository 베이스에서 강제 + 서비스에서 소유권 재확인(이중 방어) `[SEC-08][PBT-03]` (권장)

B) Repository에서만

C) 서비스 계층에서만

X) Other

[Answer]: A

## Question 7: 백업 방식(로컬 demo)
자동 백업(RES-12/02)을 로컬 환경에서 어떻게 구현할까요?

A) 스케줄된 `pg_dump` 스크립트(컨테이너/크론) + 보존 정책 문서화 (권장, demo 적합)

B) DB 볼륨 스냅샷

C) 애플리케이션 레벨 내보내기

X) Other

[Answer]: A

## Question 8: 보안 이벤트 알림 연계(RES-15/SEC-14)
보안 이벤트 알림을 어떻게 처리할까요? (기존 조직 프로세스 미지정 상태)

A) 구조적 로그에 SECURITY 레벨로 기록 + 알림 어댑터 인터페이스만 정의(실제 채널은 추후 연결) (권장, demo 적합)

B) 로그만 기록(어댑터 없음)

C) 특정 채널(웹훅 등) 지정 — [Answer]에 명시

X) Other

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 모호성/모순을 점검하고 설계 산출물을 생성합니다.
