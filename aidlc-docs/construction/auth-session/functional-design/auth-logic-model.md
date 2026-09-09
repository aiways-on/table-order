# Auth & Session Logic Model — U2 auth-session

**단계**: CONSTRUCTION → Functional Design
**기반**: U1 app/core (TenantContext, RateLimiter, Notifier, errors), app/shared (Store, Table, TableSession)
**결정**: Q1–Q7 모두 A

관리자 인증(JWT)과 테이블/고객 세션(토큰)의 비즈니스 로직을 정의한다. 인프라는 U1을 승계.

---

## 1. 관리자 로그인 (US-AUTH-01/02)
**입력**: `store_code`, `admin_username`, `password`
**흐름**:
1. RateLimiter 확인(계정+IP 키). 초과 → 429 + 보안 이벤트(Notifier). `[SEC-12]`
2. `store_code`로 Store 조회. 없으면 일반화 실패(존재 비노출). `[SEC-15]`
3. `admin_username` 일치 확인 + `bcrypt.verify(password, admin_password_hash)`.
4. 실패 → 일반화 오류 + 실패 카운트 + 보안 이벤트. 성공 → RateLimiter 리셋.
5. JWT 발급: claims `{sub: store_id, role: "admin", iat, exp: +16h, iss}`. `[SEC-08]`
6. `Set-Cookie`: HttpOnly, Secure, SameSite=Strict, Max-Age=16h. `[SEC-12]`

**JWT 검증(매 요청, 관리자 라우트)**:
- 쿠키에서 토큰 추출 → 서명·만료·iss 검증 → TenantContext(store_id, role=admin) 확립.
- 실패/만료 → 401(재인증 요구). `[SEC-08]`

## 2. 관리자 로그아웃 (Q2=A)
- 쿠키 삭제(Max-Age=0). 서버 블랙리스트 미도입 — 16h 단기 만료로 위험 제한.

## 3. 로그인 시도 제한 (US-AUTH-03, Q3=A)
- 키 = `login:{store_code}:{username}:{client_ip}`. U1 RateLimiter(기본 5회/60s).
- 초과 → 429. 모든 인증 실패는 `Notifier.notify_security_event("login_failed", ...)`. `[SEC-14]`

## 4. 테이블 초기 설정 (US-AUTH-04, 관리자 전용)
**입력**(admin JWT 필요): `table_no`, `table_password`
**흐름**:
1. 관리자 컨텍스트(store_id) 확인.
2. Table upsert: `(store_id, table_no)` 유니크. `table_password` → bcrypt 해시 저장. `[SEC-12]`
3. 응답: 테이블 식별 정보(태블릿 로컬 저장용).

## 5. 테이블/고객 세션 시작 & 자동 로그인 (US-AUTH-05, Q4/Q5/Q6=A)
**입력**: `store_code`, `table_no`, `table_password`
**흐름**:
1. Store→Table 조회, `bcrypt.verify(table_password, table_password_hash)`. 실패 → 일반화 오류 + 레이트리밋.
2. 활성 세션 규칙(Q5): 해당 table의 `status=active` 세션이 있으면 재사용, 없으면 신규 생성.
   - 신규: `session_token = secrets.token_urlsafe(32)`, `status=active`, `started_at`, 16h 수명. `[부분유니크 인덱스 준수]`
3. 응답: `session_token`(+ store_id, table_id) → 태블릿 로컬 저장(Q6).

**고객 세션 검증(매 요청, 고객 라우트)**:
- 헤더/파라미터의 `session_token` → DB 조회 → `status=active` && 미만료 확인.
- TenantContext(store_id, role=customer, table_id, session_id) 확립. `[SEC-08 객체수준 인가]`
- 무효/만료/close → 401.

## 6. 세션 종료(무효화)
- `TableSession.status=closed`, `closed_at` 설정 → 토큰 즉시 무효. (주문 이관은 U4에서 연계)

---

## U1 계약 연계
| U1 구성 | U2 사용 |
|---------|---------|
| TenantContext / set_context | 로그인·세션 검증 후 컨텍스트 확립 |
| RateLimiter | 로그인·세션 인증 시도 제한 |
| Notifier | 인증 실패 보안 이벤트 |
| errors(Unauthorized/RateLimit/Forbidden) | 일반화 오류 응답 |
| TenantScopedRepository | Table/TableSession 테넌트 스코프 접근 |
| config(jwt_secret/expire, bcrypt_rounds, login_rate_*) | 파라미터 |

## 스토리 커버리지
US-AUTH-01 ✅(§1) · US-AUTH-02 ✅(§1 JWT 16h/검증) · US-AUTH-03 ✅(§3) · US-AUTH-04 ✅(§4) · US-AUTH-05 ✅(§5)
