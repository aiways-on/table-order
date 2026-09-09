# Application Design (통합본) — 테이블오더 서비스

**단계**: INCEPTION → Application Design
**프로젝트 유형**: Greenfield · 멀티테넌트
**입력**: `requirements.md`, `stories.md`(33 스토리/5 Epic), `personas.md`, `execution-plan.md`
**세부 문서**: [components.md](./components.md) · [component-methods.md](./component-methods.md) · [services.md](./services.md) · [component-dependency.md](./component-dependency.md)

> 상세 비즈니스 로직·데이터 모델 필드·불변식 상세는 CONSTRUCTION → Functional Design(Unit별)에서 확정합니다.

---

## 1. 설계 결정 요약 (승인된 답변)
| # | 결정 | 선택 |
|---|------|------|
| Q1 | 아키텍처 스타일 | 계층형 **모듈러 모놀리스** (FastAPI, 도메인 모듈 분리) |
| Q2 | 실시간 처리 | **인메모리 이벤트 버스** + SSE (단일 인스턴스) |
| Q3 | 데이터 접근 | **Repository 패턴 + SQLAlchemy** (테넌트 스코프 강제) |
| Q4 | 멀티테넌시 | **공유 스키마 + store_id** 필터 (미들웨어 컨텍스트 주입) |
| Q5 | 토큰 전달 | 관리자 **HttpOnly Secure 쿠키(JWT)** / 고객 **로컬 세션 토큰 + 서버 검증** |
| Q6 | API 스타일 | **REST + `/api/v1`** 경로 버저닝 |

## 2. 아키텍처 개요
```text
[FE-Customer]  [FE-Admin]        (React/Vite)
      │  REST(/api/v1) + SSE
      ▼
[API Layer — FastAPI]
      ▼
[Service Layer]  Auth · Menu · Order · Session · Realtime
      ▼
[Repository Layer]  (TenantComponent 스코프 강제)
      ▼
[관계형 DB — SQLAlchemy]  Store·Menu·Table·TableSession·Order·OrderHistory
횡단: Tenant(격리/인가) · Platform(로깅·헤더·검증·헬스·백업)
```

## 3. 컴포넌트 요약
| ID | 컴포넌트 | 핵심 책임 | 스토리 |
|----|----------|-----------|--------|
| C1 | Auth | 관리자 로그인(JWT/bcrypt), 테이블 세션·자동 로그인, 토큰 검증 | US-AUTH-01~05 |
| C2 | Menu | 메뉴 CRUD·카테고리·순서·조회 | US-MENU-01~07 |
| C3 | Order | 주문 확정·조회·상태·삭제, 총액 계산 | US-ORDER-*, US-SESSION-02 |
| C4 | Session | 세션 라이프사이클·이용완료 이관·이력 | US-SESSION-01·03·04 |
| C5 | Realtime | SSE 이벤트 버스(고객/관리자 스트림) | US-ORDER-08·09·11 |
| C6 | Tenant(횡단) | store_id 격리·객체수준 인가 | US-TENANT-01 + 전역 |
| C7 | Platform(횡단) | 로깅·보안헤더·검증·헬스·백업 | US-TENANT-02~05 |

> 컴포넌트별 메서드 시그니처는 [component-methods.md](./component-methods.md) 참조.

## 4. 서비스 계층
Auth·Menu·Order·Session·Realtime·Platform 서비스가 오케스트레이션을 담당하며, 주요 흐름(주문 확정 / 상태 변경 / 세션 종료)은 [services.md](./services.md)에 시퀀스로 정리. 도메인 간 협력은 이벤트 버스·공유 Repository로 느슨하게 결합.

## 5. 의존성/통신
- 동기 호출(API→Service→Repository) + 인메모리 pub/sub + SSE(단방향) + 미들웨어 주입(Tenant/Platform).
- 도메인 컴포넌트 간 순환 호출 금지. 상세 매트릭스·데이터 흐름은 [component-dependency.md](./component-dependency.md) 참조.

## 6. 데이터 엔티티(초안 — Functional Design에서 확정)
Store, Menu, Table, TableSession, Order, OrderHistory. 모든 엔티티는 store_id로 스코프.

## 7. 확장 규칙 준수 요약 (Application Design 단계)
| 확장 | 적용 | 반영 내용 | 판정 |
|------|:---:|-----------|------|
| **Security Baseline** | 적용 | SEC-08(테넌트 격리/인가) 아키텍처화, SEC-12(인증/bcrypt/시도제한) AuthComponent, SEC-04/05/03/15(헤더/검증/로깅/오류) PlatformComponent 설계 반영 | 준수 |
| **Property-Based Testing** | 부분 | 불변식 대상(총액 PBT-03, 세션 멱등 PBT-04, 격리 PBT-03, 상태 PBT-06)을 Order/Session/Tenant 책임에 명시. 실제 테스트는 Functional/Code Gen | 준수(설계 표기) |
| **Resiliency Baseline** | 부분 | RES-10(SSE 재연결) Realtime, RES-06/12/02/05(헬스·백업·관측성) Platform 설계 반영. RES-04/08/14는 NFR Design에서 확정 | 준수(설계 표기) |

**비차단 사항**: 인메모리 이벤트 버스(Q2=A)는 단일 인스턴스 전제 — 다중 인스턴스 확장 시 외부 브로커 교체 필요(로컬 demo 범위에 부합). NFR/Infra Design에서 재확인.

## 8. 작업 단위 연계
본 설계는 Units Generation의 잠정 6개 단위(backend-core, auth-session, menu, order, frontend-customer, frontend-admin)와 정렬됨:
- backend-core ← Tenant/Platform + API 기반
- auth-session ← Auth(+ Table/TableSession)
- menu ← Menu
- order ← Order + Session + Realtime
- frontend-customer / frontend-admin ← FE 컴포넌트
