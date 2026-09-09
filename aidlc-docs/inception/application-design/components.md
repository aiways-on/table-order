# Components — 테이블오더 서비스

**단계**: INCEPTION → Application Design
**아키텍처**: 계층형 모듈러 모놀리스 (FastAPI) + React 프론트엔드 2종, 관계형 DB, 멀티테넌트(공유 스키마 + store_id)
**결정 반영**: Q1=모듈러 모놀리스, Q2=인메모리 이벤트 버스, Q3=Repository+SQLAlchemy, Q4=공유 스키마 store_id, Q5=관리자 쿠키/고객 로컬 토큰, Q6=REST /api/v1

> 상세 비즈니스 로직·데이터 모델 필드는 CONSTRUCTION → Functional Design(Unit별)에서 확정합니다.

---

## 아키텍처 개요

```text
┌───────────────────┐   ┌───────────────────┐
│  고객 태블릿 UI    │   │  관리자 대시보드 UI │   (React/Vite)
└─────────┬─────────┘   └─────────┬─────────┘
          │  REST(/api/v1) + SSE            │
          ▼                                  ▼
┌─────────────────────────────────────────────────┐
│  API Layer (FastAPI 라우터)                       │
│  auth · menu · order · session · realtime · health│
├─────────────────────────────────────────────────┤
│  Service Layer (오케스트레이션)                    │
│  Auth · Menu · Order · Session · Realtime         │
├─────────────────────────────────────────────────┤
│  Repository Layer (테넌트 스코프 강제)             │
│  Store/Menu/Table/TableSession/Order/History Repo │
├─────────────────────────────────────────────────┤
│  관계형 DB (SQLAlchemy ORM)                        │
└─────────────────────────────────────────────────┘
횡단(Cross-cutting): TenantContext · AuthN/AuthZ · Logging · SecurityHeaders/CORS · HealthCheck · Backup
```

---

## C1. AuthComponent (인증·세션)
- **목적**: 매장 관리자 인증 및 테이블/고객 세션 관리.
- **책임**:
  - 매장 관리자 로그인(자격 검증, JWT 발급, bcrypt 해시 검증) `[SEC-12]`
  - 관리자 세션 16시간 유지·검증·만료 처리 `[SEC-08]`
  - 로그인 시도 제한(브루트포스 방지) `[SEC-12]` `[SEC-14]`
  - 테이블 태블릿 초기 설정 및 고객 자동 로그인 세션 발급
  - 토큰 서버측 검증(서명·만료·발급자)
- **인터페이스(요약)**: `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `POST /api/v1/tables/{id}/provision`, `POST /api/v1/tables/{id}/auto-login`
- **관련 스토리**: US-AUTH-01~05
- **엔티티**: Store, Table, TableSession(세션 토큰)

## C2. MenuComponent (메뉴)
- **목적**: 매장 메뉴 관리 및 고객 메뉴 조회.
- **책임**:
  - 메뉴 CRUD(등록/수정/삭제) — 자기 매장만 `[SEC-08 IDOR]`
  - 카테고리 분류, 노출 순서 조정
  - 가격/필수 필드 입력 검증 `[SEC-05]` `[PBT-03 가격 범위]`
  - 고객용 카테고리별 메뉴 조회
- **인터페이스(요약)**: `GET /api/v1/menus`, `POST/PUT/DELETE /api/v1/menus/{id}`, `PUT /api/v1/menus/order`
- **관련 스토리**: US-MENU-01~07
- **엔티티**: Menu

## C3. OrderComponent (주문)
- **목적**: 주문 확정·조회·상태 관리(장바구니는 클라이언트 로컬).
- **책임**:
  - 주문 확정(장바구니 페이로드 검증→주문 생성), 주문번호 발급 `[SEC-05]`
  - 총액 계산·검증 `[PBT-03 총액 불변식]`
  - 현재 세션 주문 조회(고객) / 테이블별 주문 조회·필터(관리자) `[SEC-08]`
  - 주문 상태 변경(대기중→준비중→완료), 주문 직권 삭제 `[SEC-13 감사]`
  - 상태 변경 시 RealtimeComponent로 이벤트 발행
- **인터페이스(요약)**: `POST /api/v1/orders`, `GET /api/v1/orders`, `PATCH /api/v1/orders/{id}/status`, `DELETE /api/v1/orders/{id}`
- **관련 스토리**: US-ORDER-01~12, US-SESSION-02
- **엔티티**: Order, (읽기) TableSession

## C4. SessionComponent (테이블 세션·이력)
- **목적**: 테이블 세션 라이프사이클과 주문 이력 관리.
- **책임**:
  - 첫 주문 시 세션 시작, 이후 주문 세션 귀속
  - 이용 완료(세션 종료): 주문→OrderHistory 이관, 총액 리셋, 완료 시각 기록 `[PBT-04 멱등성]` `[PBT-06 상태]`
  - 과거 주문 이력 조회(테이블별, 날짜 필터) — 자기 매장만 `[SEC-08]`
- **인터페이스(요약)**: `POST /api/v1/tables/{id}/close-session`, `GET /api/v1/tables/{id}/history`
- **관련 스토리**: US-SESSION-01·03·04
- **엔티티**: TableSession, OrderHistory

## C5. RealtimeComponent (실시간 SSE)
- **목적**: SSE 기반 실시간 이벤트 전달(고객 주문 상태·관리자 모니터링).
- **책임**:
  - 인메모리 이벤트 버스 pub/sub(매장·테이블 토픽 스코프) `[SEC-08]`
  - 고객 SSE 스트림(현재 세션 주문 상태), 관리자 SSE 스트림(신규 주문·상태)
  - 연결 관리·타임아웃·재연결 지원(Last-Event-ID) `[RES-10]`
  - 연결/지연 메트릭 노출 `[RES-05]`
- **인터페이스(요약)**: `GET /api/v1/stream/customer` (SSE), `GET /api/v1/stream/admin` (SSE)
- **관련 스토리**: US-ORDER-08·09·11

## C6. TenantComponent (횡단 — 멀티테넌시/인가)
- **목적**: 매장 단위 데이터 격리와 인가 강제.
- **책임**:
  - 요청에서 store_id 컨텍스트 결정(토큰 기반) 및 주입
  - 모든 리포지토리 쿼리에 store_id 스코프 강제 `[SEC-08 IDOR 방지]` `[PBT-03 격리 불변식]`
  - 객체 수준 인가(리소스 소유권 확인)
- **인터페이스(요약)**: 미들웨어/의존성 주입(`get_tenant_context`), 리포지토리 베이스에 스코프 적용
- **관련 스토리**: US-TENANT-01, 전 도메인 횡단

## C7. PlatformComponent (횡단 — 플랫폼/운영)
- **목적**: 보안·관측성·복원력 횡단 관심사.
- **책임**:
  - 구조적 로깅(상관ID, 민감정보 마스킹) `[SEC-03]`, 보안 이벤트 알림 훅 `[SEC-14]` `[RES-15]`
  - 보안 헤더(CSP/HSTS/…) 및 CORS 화이트리스트 `[SEC-04]` `[SEC-08]`
  - 입력 검증 공통 처리 및 오류 표준화(fail-closed) `[SEC-05]` `[SEC-15]`
  - 헬스체크(shallow/deep) `[RES-06]`, DB 백업 훅 `[RES-12]` `[RES-02]`
- **인터페이스(요약)**: `GET /health`, `GET /health/deep`, 미들웨어(로깅/헤더/오류), 백업 스케줄 훅
- **관련 스토리**: US-TENANT-02·03·04·05

---

## 프론트엔드 컴포넌트
- **FE-Customer** (React/Vite): 자동 로그인 → 메뉴(카테고리/상세) → 장바구니(로컬 저장) → 주문 확정 → 현재 세션 내역(SSE). 터치 최적화(≥44px).
- **FE-Admin** (React/Vite): 매장 로그인 → 테이블 그리드 실시간 모니터링(SSE) → 주문 상세/상태 변경/삭제 → 테이블/세션 관리 → 메뉴 관리 → 과거 이력.
