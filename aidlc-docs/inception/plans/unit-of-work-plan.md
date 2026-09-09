# Unit of Work 계획 (Part 1: Planning)

**단계**: INCEPTION → Units Generation
**목적**: 시스템을 개발 관리 가능한 작업 단위(Unit of Work)로 분해
**입력**: `requirements.md`, `stories.md`(33 스토리), `application-design.md`(7 컴포넌트), `execution-plan.md`

이 문서는 (1) 단위 분해 실행 체크리스트와 (2) 분해 방향 결정 질문을 담고 있습니다.
아래 **"질문"**의 각 `[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 승인 후 단위 산출물을 생성합니다.

---

## A. 단위 분해 실행 체크리스트 (승인 후 Part 2에서 수행)

- [x] `unit-of-work.md` 생성 — 단위 정의·책임 + (그린필드) 코드 조직 전략
- [x] `unit-of-work-dependency.md` 생성 — 단위 간 의존성 매트릭스·빌드/개발 순서
- [x] `unit-of-work-story-map.md` 생성 — 33개 스토리를 단위에 매핑(누락 0)
- [x] 단위 경계·의존성 검증
- [x] 모든 스토리가 단위에 배정되었는지 확인

---

## B. 잠정 단위 구성 (설계 기반 초안 — 답변 후 확정)

| 단위 | 유형 | 컴포넌트 | 대표 스토리 |
|------|------|----------|-------------|
| **U1. backend-core** | Module | Tenant, Platform, API 기반, DB/마이그레이션 | US-TENANT-01~05 |
| **U2. auth-session** | Module | Auth (Store/Table/TableSession) | US-AUTH-01~05 |
| **U3. menu** | Module | Menu | US-MENU-01~07 |
| **U4. order** | Module | Order, Session, Realtime(SSE) | US-ORDER-01~12, US-SESSION-01~04 |
| **U5. frontend-customer** | Module | FE-Customer(React) | 고객측 US-AUTH-05, MENU, ORDER |
| **U6. frontend-admin** | Module | FE-Admin(React) | 관리자측 US-AUTH, MENU, ORDER, SESSION |

> 배포 모델: 단일 백엔드(모듈러 모놀리스) + 2개 프론트엔드 앱, 로컬 docker-compose. 단위=논리 모듈.

---

## C. 질문 (Decomposition Questions)

## Question 1: 단위 분해 입도(그룹핑 전략)
스토리를 어떤 단위로 묶을까요?

A) 도메인 모듈 기준 6단위 — backend-core / auth-session / menu / order(+session+realtime) / frontend-customer / frontend-admin (권장, 설계와 정렬)

B) 더 세분화 8단위 — order와 session·realtime을 분리, 인증과 세션 분리

C) 더 크게 3단위 — backend / frontend-customer / frontend-admin

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: order 단위 내 session/realtime 처리
주문·세션·실시간(SSE)의 단위 배치를 어떻게 할까요?

A) 하나의 order 단위로 통합 — 주문·세션 이력·SSE가 강하게 결합되어 함께 개발 (권장)

B) order / session-history / realtime 3개로 분리

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: 백엔드 배포 모델
백엔드 배포 형태를 어떻게 할까요?

A) 단일 배포 모듈러 모놀리스 — 하나의 FastAPI 서비스, 내부 도메인 모듈 분리 (로컬 demo/MVP 권장)

B) 도메인별 마이크로서비스 다중 배포

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: 코드 디렉터리 구조 (그린필드)
저장소/디렉터리 구조를 어떻게 잡을까요?

A) 모노레포 — `backend/`(app/도메인 모듈), `frontend-customer/`, `frontend-admin/`, `docker-compose.yml` 루트 (권장)

B) 폴리레포 — 단위별 별도 저장소

C) 백엔드 도메인별 폴더 + 프론트 통합(단일 앱, 라우팅으로 고객/관리자 분리)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5: 단위 개발/빌드 순서
개발·빌드 순서를 어떻게 할까요?

A) backend-core → auth-session → menu → order → frontend-customer/admin (의존성 기반 순차, 권장)

B) 백엔드 전체 → 프론트 전체

C) 수직 슬라이스(기능별로 백+프론트 동시)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6: 공유 자원(모델/스키마) 관리
단위 간 공유 모델/타입을 어떻게 관리할까요?

A) 백엔드 내 공용 모듈(shared: DB 모델·Pydantic 스키마), 프론트는 각자 API 타입 정의 (권장)

B) OpenAPI 스키마에서 프론트 타입 자동 생성

C) 공유 패키지 별도 관리

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 답변의 모호성/모순을 점검하고 계획을 확정한 뒤 승인을 요청합니다.
