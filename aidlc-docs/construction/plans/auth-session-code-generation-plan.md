# Code Generation 계획 — U2 auth-session (Part 1: Planning)

**단계**: CONSTRUCTION → Code Generation
**단위**: U2 auth-session
**코드 위치**: `backend/app/auth/` (앱 코드), 문서 `aidlc-docs/construction/auth-session/code/`
**이 계획이 Code Generation의 단일 진실 원천입니다.**

---

## 단위 컨텍스트
**구현 스토리**: US-AUTH-01(관리자 로그인), US-AUTH-02(16h 세션), US-AUTH-03(시도 제한), US-AUTH-04(테이블 초기설정), US-AUTH-05(고객 자동 로그인)

**의존성(승계)**: U1 `app/core`(config, context, errors, ratelimit, notifier, database), `app/shared`(models: Store/Table/TableSession, repository, schemas). **하위 소비자**: U4 order(세션 컨텍스트), U5/U6 프론트(로그인/세션 API).

**소유 로직**: 인증·세션 서비스/라우터/스키마. 모델은 U1 shared 재사용(신규 테이블 없음 → 마이그레이션 불필요).

**제공 계약(다른 단위/프론트용)**:
- `require_admin` / `require_customer` 의존성(라우트 가드)
- `POST /api/v1/auth/admin/login`, `POST /auth/admin/logout`
- `POST /api/v1/auth/tables` (관리자, 테이블 설정)
- `POST /api/v1/auth/sessions` (세션 시작/자동 로그인), `DELETE /auth/sessions/{id}` (종료)

---

## 실행 단계 (Numbered Steps)

### Step 1: 모듈 구조
- [x] `app/auth/__init__.py`, 패키지 스캐폴딩
- 경로: `backend/app/auth/`

### Step 2: 보안 프리미티브 (Business Logic)
- [x] `app/auth/security.py` (bcrypt hash/verify [SEC-12], JWT encode/decode [SEC-08], secrets 토큰 생성)
- 경로: `backend/app/auth/`

### Step 3: 스키마 (API Layer 계약)
- [x] `app/auth/schemas.py` (AdminLoginRequest/Response, TableSetupRequest, SessionStartRequest/Response — Pydantic 검증 [SEC-05])
- 경로: `backend/app/auth/`

### Step 4: 서비스 (Business Logic)
- [x] `app/auth/service.py` (AuthService: admin_login, verify_admin_token, setup_table, start_session, verify_session, close_session; RateLimiter+Notifier 연계) — BR-A01~A17
- 경로: `backend/app/auth/`

### Step 5: 라우트 가드 (의존성)
- [x] `app/auth/dependencies.py` (require_admin: JWT 쿠키 검증→컨텍스트; require_customer: session_token 검증→컨텍스트) [SEC-08]
- 경로: `backend/app/auth/`

### Step 6: API 라우터
- [x] `app/auth/router.py` (admin login/logout, table setup[admin], session start/close; 쿠키 설정 [SEC-12])
- [x] `app/main.py`에 auth 라우터 등록 (기존 파일 수정)
- 경로: `backend/app/auth/`, `backend/app/main.py`

### Step 7: 단위 + 속성 테스트 (PBT)
- [x] `tests/test_auth_security.py` (Hypothesis: bcrypt verify 불변식 BR-A18, JWT round-trip/변조 BR-A20) [PBT-07]
- [x] `tests/test_auth_service.py` (로그인 성공/실패/레이트리밋, 세션 시작/검증/만료·close 무효 BR-A19) [PBT-03]
- [x] `tests/test_auth_api.py` (로그인 쿠키, 가드 401/403, 세션 흐름)
- 경로: `backend/tests/`

### Step 8: 문서
- [x] `aidlc-docs/construction/auth-session/code/code-summary.md`
- 경로: `aidlc-docs/construction/auth-session/code/`

---

## 스토리 추적성
| 스토리 | 구현 위치 | 상태 |
|--------|-----------|:---:|
| US-AUTH-01 관리자 로그인 | security.py, service.admin_login, router | [x] |
| US-AUTH-02 16h 세션 | security(JWT exp), dependencies.require_admin | [x] |
| US-AUTH-03 시도 제한 | service(RateLimiter), notifier | [x] |
| US-AUTH-04 테이블 설정 | service.setup_table, router(admin) | [x] |
| US-AUTH-05 자동 로그인 | service.start_session/verify_session, require_customer | [x] |

---

## 범위 요약
- **총 8단계**. 신규 DB 테이블 없음(U1 shared 모델 재사용) → 마이그레이션 불필요.
- 배포 아티팩트 변경 없음(기존 compose/backend 이미지에 포함).
- 테스트는 생성만, 실행은 Build & Test. 생성 후 로컬 pytest로 검증 예정.

---

**이 계획을 승인하시면 Part 2(코드 생성)로 진행합니다.**
