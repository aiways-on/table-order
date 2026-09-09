# Functional Design 계획 — U2 auth-session (Part 1: Planning)

**단계**: CONSTRUCTION → Functional Design
**단위**: U2 auth-session (관리자 인증 + 테이블/고객 세션 인증)
**입력**: stories.md(US-AUTH-01~05), U1 산출물(app/core context/middleware/errors/ratelimit/notifier, app/shared models: Store/Table/TableSession), tech-stack-decisions.md
**성격**: 인증·세션 비즈니스 로직 설계 (U1 core 인프라 위에 구축)

**적응형 단계 평가**: U2는 Functional Design + Code Generation만 실행. NFR Requirements/NFR Design/Infrastructure Design은 U1에서 확정된 횡단 NFR·패턴·공유 인프라를 승계(스킵).

`[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 산출물을 생성합니다.

---

## A. 실행 체크리스트

- [x] `auth-logic-model.md` — 관리자 로그인/JWT/세션검증, 테이블·고객 세션 로직
- [x] `auth-business-rules.md` — 인증·세션 비즈니스 규칙(BR-A*) + 확장 매핑
- [x] 스토리 US-AUTH-01~05 커버리지 확인
- [x] U1 계약(TenantContext, TenantScopedRepository, RateLimiter, Notifier) 연계 확인

---

## B. 설계 초안 (답변 후 확정)
- **관리자 로그인**: store_code + admin_username + password → bcrypt 검증 → JWT(16h) → HttpOnly/Secure/SameSite 쿠키
- **JWT 클레임**: sub(store_id), role=admin, exp(16h), iat, iss
- **테이블 세션**: 관리자 초기설정(table_no + table_password) → TableSession(active, session_token, 16h) 생성 → 태블릿 자동 로그인
- **고객 세션 검증**: session_token → 서버 검증 → TenantContext(store_id, role=customer, table_id, session_id)
- **레이트리밋**: 로그인 실패 계정/IP 기준(U1 RateLimiter 사용), 실패는 보안 이벤트(Notifier)

---

## C. 질문 (Functional Design Questions)

## Question 1: 관리자 로그인 식별 조합
로그인 시 매장 식별을 어떻게 받을까요?

A) store_code + admin_username + password (매장 코드로 테넌트 특정, 권장)

B) admin_username + password (전역 유니크 username 가정)

X) Other

[Answer]: A

## Question 2: 관리자 세션 무효화(로그아웃)
JWT 로그아웃/무효화를 어떻게 처리할까요?

A) 쿠키 삭제 + 클라이언트 만료. 서버 블랙리스트 미도입(16h 단기 만료로 위험 제한, demo 적정) (권장)

B) 서버측 토큰 블랙리스트(revocation store) 도입

X) Other

[Answer]: A

## Question 3: 로그인 시도 제한 방식 (SEC-12)
브루트포스 방지를 어떻게 구현할까요?

A) 계정+IP 키로 슬라이딩 윈도우 제한(U1 RateLimiter, 예: 5회/분) → 초과 시 429, 보안 이벤트 로깅/알림 (권장)

B) 계정 잠금(N회 실패 시 일정 시간 완전 잠금)

C) 점진적 지연(exponential backoff)

X) Other

[Answer]: A

## Question 4: 테이블 세션 토큰 생성·수명
테이블/고객 세션 토큰을 어떻게 발급할까요?

A) 암호학적 난수 토큰(secrets, DB 저장) + 16h 수명, 세션 close 시 무효화 (권장)

B) 테이블용 JWT 발급

X) Other

[Answer]: A

## Question 5: 세션과 주문 관계 (활성 세션 규칙)
테이블당 활성 세션을 어떻게 관리할까요?

A) 테이블당 활성 세션 1개(U1 부분유니크 인덱스 준수). 초기설정/재개 시 기존 active 재사용 또는 신규 생성 (권장)

B) 테이블당 다중 동시 세션 허용

X) Other

[Answer]: A

## Question 6: 자동 로그인 저장 정보 (US-AUTH-05)
태블릿 자동 로그인에 무엇을 저장할까요?

A) 클라이언트(태블릿)에 store_code+table_no+table_password(또는 발급 토큰) 로컬 저장, 서버는 세션 토큰 검증만 (권장, 프론트 U5 연계)

B) 서버가 디바이스 등록 관리

X) Other

[Answer]: A

## Question 7: 비밀번호 정책·해시 파라미터
비밀번호 처리를 어떻게 확정할까요?

A) bcrypt(cost 12, U1 설정 승계), 최소 길이 검증, 평문 저장 금지 (권장)

B) 다른 해시(argon2 등)

X) Other

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 모호성/모순을 점검하고 설계 산출물을 생성합니다.
