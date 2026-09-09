# Application Design 계획 (Part 1: Planning)

**단계**: INCEPTION → Application Design
**목적**: 상위 수준 컴포넌트 식별 및 서비스 계층 설계 (상세 비즈니스 로직은 이후 Functional Design에서)
**입력**: `requirements.md`, `stories.md`(33 스토리/5 Epic), `personas.md`, `execution-plan.md`

이 문서는 (1) Application Design 실행 체크리스트와 (2) 설계 방향 결정을 위한 질문을 담고 있습니다.
아래 **"질문"** 섹션의 각 `[Answer]:` 태그를 채운 뒤 알려주시면, 계획을 확정하고 승인 후 설계 산출물을 생성합니다.

---

## A. 설계 실행 체크리스트 (승인 후 Part 2에서 수행)

- [x] `components.md` 생성 — 컴포넌트 정의·책임·인터페이스
- [x] `component-methods.md` 생성 — 메서드 시그니처·입출력 타입·상위 목적 (상세 규칙은 Functional Design)
- [x] `services.md` 생성 — 서비스 정의·책임·오케스트레이션 패턴
- [x] `component-dependency.md` 생성 — 의존성 매트릭스·통신 패턴·데이터 흐름
- [x] `application-design.md` 생성 — 위 문서 통합본
- [x] 설계 완전성·일관성 검증
- [x] 확장 규칙(보안/복원력/PBT) 설계 반영 표기

---

## B. 잠정 아키텍처 (설계 초안 — 질문 답변 후 확정)

**계층형 아키텍처** (그린필드, FastAPI + React + 관계형 DB, 멀티테넌트):

```text
[React 고객 UI] [React 관리자 UI]
        │  (REST + SSE)
        ▼
[API Layer — FastAPI 라우터/엔드포인트]
        │
[Service Layer — 오케스트레이션]
  AuthService · MenuService · OrderService · SessionService · RealtimeService
        │
[Domain/Repository Layer — 데이터 접근, 테넌트 스코프]
        │
[관계형 DB — Store, Menu, Table, TableSession, Order, OrderHistory]

횡단(Cross-cutting): TenantContext · AuthN/AuthZ · Logging · SecurityHeaders · HealthCheck
```

**잠정 컴포넌트**:
1. **AuthComponent** — 매장 로그인(JWT/bcrypt), 테이블 세션/자동 로그인, 토큰 검증
2. **MenuComponent** — 메뉴 CRUD, 카테고리, 노출 순서
3. **OrderComponent** — 장바구니→주문 확정, 주문 상태, 조회
4. **SessionComponent** — 테이블 세션 라이프사이클, 이용 완료→이력 이동
5. **RealtimeComponent** — SSE 이벤트 발행/구독(고객 상태·관리자 모니터링)
6. **TenantComponent** (횡단) — 매장 격리, 인가, 요청 스코프
7. **PlatformComponent** (횡단) — 로깅, 보안 헤더/CORS, 헬스체크, 백업 훅

---

## C. 질문 (Design Questions)

## Question 1: 아키텍처 스타일
백엔드 컴포넌트 구성 방식을 어떻게 할까요?

A) 계층형 모듈러 모놀리스 — 단일 FastAPI 앱 내에서 도메인별 모듈(auth/menu/order/session) 분리 (로컬 demo/MVP에 권장)

B) 도메인별 마이크로서비스 — 서비스별 독립 배포(각자 API/DB)

C) 헥사고날(포트&어댑터) — 도메인 중심, 인프라 어댑터 분리 (테스트·격리에 유리, 초기 오버헤드)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: 실시간(SSE) 처리 구조
SSE 실시간 이벤트를 어떻게 구성할까요?

A) 인메모리 이벤트 버스/브로커 — 앱 내 pub/sub로 SSE 스트림에 전달 (단일 인스턴스 로컬 demo에 권장)

B) 외부 메시지 브로커(Redis Pub/Sub 등) — 다중 인스턴스 확장 대비

C) DB 폴링 기반 — 주기적 조회로 변경 감지 (단순하나 지연·부하)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: 데이터 접근 계층 패턴
DB 접근을 어떤 패턴으로 설계할까요?

A) Repository 패턴 + ORM(SQLAlchemy) — 테넌트 스코프를 리포지토리에서 강제, PBT/테스트 용이 (권장)

B) ORM 직접 사용(서비스에서 세션 직접 조작) — 단순하나 격리 로직 분산

C) Raw SQL + 쿼리 빌더 — 세밀 제어, 보일러플레이트 증가

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: 멀티테넌시 격리 방식
매장(테넌트) 데이터 격리를 어떻게 구현할까요?

A) 공유 스키마 + tenant_id(store_id) 컬럼 필터링 — 모든 쿼리에 스코프 강제, 미들웨어로 컨텍스트 주입 (demo/MVP에 권장)

B) 테넌트별 스키마 분리

C) 테넌트별 DB 분리

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5: 인증 토큰 전달 방식
관리자 JWT와 고객/테이블 세션 토큰을 어떻게 전달·저장할까요?

A) 관리자=HttpOnly Secure 쿠키(JWT), 고객 태블릿=로컬 저장 세션 토큰 + 서버 검증 (보안 확장에 부합, 권장)

B) 양쪽 모두 Authorization 헤더(Bearer) + 클라이언트 저장

C) 양쪽 모두 쿠키 기반

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6: API 스타일/버저닝
API 인터페이스 스타일을 어떻게 할까요?

A) REST + `/api/v1` 경로 버저닝, 리소스 중심 엔드포인트 (권장)

B) REST, 버저닝 없음 (demo 단순화)

C) RPC 스타일(액션 중심 엔드포인트)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 답변의 모호성/모순을 점검하고 계획을 확정한 뒤 승인을 요청합니다.
