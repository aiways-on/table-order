# Code Generation 계획 — U1 backend-core (Part 1: Planning)

**단계**: CONSTRUCTION → Code Generation
**단위**: U1 backend-core (횡단 기반: core 인프라 + shared 도메인 모델 + Tenant/Platform)
**프로젝트 타입**: Greenfield / 모노레포 / 모듈러 모놀리스
**코드 위치**: 워크스페이스 루트 `backend/` (앱 코드), 문서는 `aidlc-docs/construction/backend-core/code/`
**이 계획이 Code Generation의 단일 진실 원천(single source of truth)입니다.**

---

## 단위 컨텍스트 (Unit Context)

**구현 스토리** (US-TENANT-01~05 — 횡단 기반):
- US-TENANT-01: 매장(테넌트) 데이터 격리 (store_id 스코프) — `[SEC-08][PBT-03]`
- US-TENANT-02: 교차 테넌트 접근 차단 (403/빈 결과, 존재 비노출)
- US-TENANT-03: 구조적 로깅·상관ID·민감정보 마스킹 — `[SEC-03]`
- US-TENANT-04: 헬스체크(shallow/deep)·백업 — `[RES-06][RES-12]`
- US-TENANT-05: 보안 이벤트 알림 어댑터 — `[SEC-14][RES-15]`

**의존성**: 없음(U1은 최하위 기반). **하위 소비자**: U2 auth, U3 menu, U4 order (shared 모델·core 인프라 승계).

**소유 엔티티(공용)**: Store, Menu, Table, TableSession, Order, OrderHistory (SQLAlchemy 모델 정의는 U1; 도메인 서비스/라우터는 각 단위).

**서비스 경계**: U1은 core 인프라 + shared 모델 + Tenant/Platform 횡단 기능만. 인증/메뉴/주문 비즈니스 로직은 후속 단위.

---

## 실행 단계 (Numbered Steps)

### Step 1: 프로젝트 구조 셋업 (greenfield)
- [x] `backend/` 스캐폴딩: `app/`, `app/core/`, `app/shared/`, `alembic/`, `tests/`
- [x] `pyproject.toml`(의존성), `.env.example`, `.gitignore`, `README.md`
- [x] `app/main.py`(FastAPI 앱 팩토리, 미들웨어·라우터·핸들러 등록, lifespan)
- 경로: `backend/`

### Step 2: Core — 설정·DB (Business Logic: 인프라 기반)
- [x] `app/core/config.py` (pydantic-settings: DB URL, JWT, CORS, pool, timeouts) `[SEC-01]`
- [x] `app/core/database.py` (SQLAlchemy 2.0 엔진/세션 팩토리, 풀, get_db Depends, Base) `[NFR-S2]`
- 경로: `backend/app/core/`

### Step 3: Core — 테넌트 컨텍스트·미들웨어·보안
- [x] `app/core/context.py` (TenantContext ContextVar: store_id/role/session) `[SEC-08]`
- [x] `app/core/middleware.py` (CorrelationId, SecurityHeaders) `[SEC-04]`
- [x] `app/core/logging.py` (구조적 JSON 로그 + 마스킹) `[SEC-03]`
- [x] `app/core/errors.py` (중앙 예외 핸들러, fail-closed, 일반화 응답) `[SEC-15]`
- [x] `app/core/notifier.py` (Notifier 인터페이스 + LogNotifier) `[SEC-14][RES-15]`
- [x] `app/core/ratelimit.py` (인메모리 레이트리밋) `[SEC-11]`
- 경로: `backend/app/core/`

### Step 4: Core — 이벤트버스·헬스·메트릭
- [x] `app/core/events.py` (인메모리 EventBus pub/sub, asyncio 큐) `[NFR-P2]`
- [x] `app/core/health.py` (shallow/deep 헬스 라우터) `[RES-06]`
- [x] `app/core/metrics.py` (요청/지연/오류/SSE 카운터) `[RES-05]`
- 경로: `backend/app/core/`

### Step 5: Shared — 도메인 모델 (Repository Layer 기반)
- [x] `app/shared/models.py` (Store/Menu/Table/TableSession/Order/OrderHistory, UUID PK, soft-delete, store_id, 복합 인덱스, UTC) — domain-entities.md 반영
- [x] `app/shared/repository.py` (TenantScopedRepository 베이스: store_id 강제 필터·소유권 검증) `[SEC-08][PBT-03]`
- [x] `app/shared/schemas.py` (공통 Pydantic 스키마: 에러, 페이지네이션, 헬스)
- 경로: `backend/app/shared/`

### Step 6: 비즈니스 로직 단위 테스트 + 속성 테스트 (PBT)
- [x] `tests/test_tenant_isolation.py` (Hypothesis: 교차 테넌트 접근 불변식) `[PBT-03]`
- [x] `tests/test_repository.py` (TenantScopedRepository 필터·소유권)
- [x] `tests/test_logging_masking.py` (민감정보 마스킹) `[SEC-03]`
- [x] `tests/test_health.py`, `tests/conftest.py` (테스트 DB 픽스처) `[PBT-06]`
- 경로: `backend/tests/`

### Step 7: 데이터베이스 마이그레이션
- [x] `alembic.ini`, `alembic/env.py`, 초기 마이그레이션(6개 엔티티 + 인덱스 + partial-unique active session) `[NFR-M2]`
- 경로: `backend/alembic/`

### Step 8: 배포 아티팩트
- [x] `backend/Dockerfile` (python:3.12-slim, uvicorn, entrypoint: alembic upgrade → uvicorn)
- [x] 루트 `docker-compose.yml` (db/backend/backup 서비스, volumes, healthcheck, network) — deployment-architecture.md 반영
- [x] `backend/scripts/backup.sh` (pg_dump 스케줄) `[RES-12]`
- 경로: 워크스페이스 루트 + `backend/`

### Step 9: 문서 생성 (markdown 요약)
- [x] `aidlc-docs/construction/backend-core/code/code-summary.md` (생성 파일 목록·구조·실행법·스토리 추적성)
- 경로: `aidlc-docs/construction/backend-core/code/`

---

## 스토리 추적성 (Story Traceability)
| 스토리 | 구현 위치 | 상태 |
|--------|-----------|:---:|
| US-TENANT-01 격리 | shared/repository.py, context.py, models(store_id) | [x] |
| US-TENANT-02 교차차단 | repository.py(빈결과/403), errors.py | [x] |
| US-TENANT-03 로깅 | core/logging.py, middleware.py | [x] |
| US-TENANT-04 헬스/백업 | core/health.py, scripts/backup.sh, compose | [x] |
| US-TENANT-05 알림 | core/notifier.py | [x] |

---

## 범위 요약
- **총 9단계**, 예상 산출: backend 스캐폴딩 + core 인프라 12+ 모듈 + shared 모델/리포지토리 + PBT 포함 테스트 + Alembic 마이그레이션 + Docker/compose 배포 아티팩트.
- **테스트는 여기서 생성만**, 실행은 Build & Test 단계.
- 확장 규칙(SEC/PBT/RES) 각 파일에 태그로 추적.

---

**이 계획을 승인하시면 Part 2(코드 생성)로 진행합니다.** 수정 요청도 가능합니다.
