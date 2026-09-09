# Code Summary — U2 auth-session

**Phase**: CONSTRUCTION → Code Generation (Part 2 완료)
**Unit**: U2 auth-session
**Stories**: US-AUTH-01~05 (모두 구현·검증)
**검증**: 로컬 throwaway venv에서 `pytest` 실행 → **38 passed** (U1 14 + U2 24). venv는 커밋하지 않고 삭제함.

---

## 생성/수정 파일

### 앱 코드 (`backend/app/auth/`)
| 파일 | 내용 | 관련 규칙 |
|------|------|-----------|
| `__init__.py` | 패키지 스캐폴딩 | — |
| `security.py` | bcrypt hash/verify(ValueError/TypeError→False), JWT HS256(sub/role/iss/iat/exp+16h) encode/decode(require exp·iss·sub, InvalidTokenError→None), `secrets.token_urlsafe(32)` 세션 토큰 | SEC-08, SEC-12, SEC-15 |
| `schemas.py` | AdminLoginRequest(password min 8)/Response, TableSetupRequest(table_no≥1, pw min 4)/Response, SessionStartRequest, SessionResponse, MessageResponse — Pydantic 검증 | SEC-05 |
| `service.py` | `AuthService`: admin_login(레이트리밋→bcrypt→JWT, 실패 시 일반화 오류·보안 이벤트 알림), setup_table(생성/갱신), start_session(테이블 pw 검증→활성 세션 재사용/만료 세션 정리 후 신규), verify_session(활성·비만료), close_session(store 소유권 재확인→NotFound) | BR-A01~A17, SEC-08/11/12/15 |
| `dependencies.py` | `require_admin`(JWT 쿠키→ADMIN 컨텍스트), `require_customer`(X-Session-Token→CUSTOMER 컨텍스트), `client_ip`, `get_auth_service` | SEC-08, SEC-12 |
| `router.py` | 엔드포인트 + HttpOnly·SameSite=Strict·(prod)Secure 쿠키 설정 | SEC-04, SEC-12 |

### 수정된 U1 파일
| 파일 | 변경 | 사유 |
|------|------|------|
| `app/main.py` | auth 라우터 등록 | U2 배선 |
| `app/core/errors.py` | AppError 핸들러 로그의 `message=` → `detail=` | **버그 수정**: `_StructuredLogger.info(message, **ctx)`의 위치 인자명 `message`와 충돌하여 모든 4xx 응답이 500 TypeError로 전환되던 문제. U1 테스트가 이 경로를 밟지 않아 U2에서 처음 노출됨. |
| `pyproject.toml` | `bcrypt>=4.0,<4.1` 핀 추가 | passlib 1.7.4가 제거된 `bcrypt.__about__`를 참조 → 4.1+ 비호환 |

### 테스트 (`backend/tests/`)
| 파일 | 커버리지 |
|------|----------|
| `test_auth_security.py` | Hypothesis PBT: bcrypt round-trip(BR-A18), JWT round-trip/변조 거부(BR-A20), 세션 토큰 유일성. NUL·>72바이트는 bcrypt 도메인 밖이라 생성기에서 제외 |
| `test_auth_service.py` | 로그인 성공/오답/미존재 store/레이트리밋/성공 시 카운터 리셋, setup_table 생성·갱신, start_session 재사용·오답·미존재, verify_session 정상·만료(BR-A19)·close 후 무효, close_session 교차 store→NotFound(BR-A17) |
| `test_auth_api.py` | TestClient(StaticPool SQLite, get_db 오버라이드): 로그인 쿠키(HttpOnly/SameSite), 자격오류 일반화(비밀번호 미노출), 짧은 pw 422, 미인증 가드 401, 전체 흐름(로그인→테이블 설정→세션 시작→종료→재종료 401), 로그아웃 |

---

## 제공 계약 (하위 단위/프론트)
- 가드: `require_admin`, `require_customer` (Depends) — U3 menu, U4 order에서 재사용
- `POST /api/auth/admin/login` (쿠키 발급), `POST /api/auth/admin/logout`
- `POST /api/auth/tables` (관리자, 테이블 pw 설정)
- `POST /api/auth/sessions` (세션 시작/자동 로그인), `POST /api/auth/sessions/close` (고객 종료)

> **계획 대비 경로 조정**: 계획 초안의 예시 경로(`/api/v1/...`, `DELETE /sessions/{id}`) 대신 U1 라우팅 관례(`/api/...`)와 컨텍스트 기반 종료(`/sessions/close`, 세션 id를 URL에 노출하지 않음 → SEC-15)를 채택. 기능·계약은 동일.

## 확장 규칙 준수 요약
| 확장 | 상태 | 근거 |
|------|:---:|------|
| Security Baseline | ✅ | 쿠키 HttpOnly/SameSite=Strict/(prod)Secure(SEC-12), CORS 명시 오리진, JWT 서명·iss·exp 검증(SEC-08), 레이트리밋(SEC-11), 자격오류 일반화·store 소유권 재확인·세션 id URL 미노출(SEC-15), 비밀번호·토큰 로깅 마스킹(SEC-03, U1) |
| Property-Based Testing | ✅ | Hypothesis 불변식 3종(BR-A18/A19/A20), 세션 격리 재사용(PBT-03) |
| Resiliency Baseline | ✅(해당) | fail-closed 오류 처리, 만료 세션 정리; 인프라·백업 항목은 U1에서 확정(N/A) |

---

## 마이그레이션 / 배포
- **신규 DB 테이블 없음** — U1 shared 모델(Store/Table/TableSession) 재사용 → Alembic 마이그레이션 불필요.
- 배포 아티팩트 변경 없음 — 기존 compose/backend 이미지에 포함.
