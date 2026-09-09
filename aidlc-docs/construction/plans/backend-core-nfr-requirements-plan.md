# NFR Requirements 계획 — U1 backend-core

**단계**: CONSTRUCTION → NFR Requirements (Part 1: Planning)
**단위**: U1 backend-core
**입력**: U1 functional-design 산출물, `requirements.md`(NFR), 확장(SEC/RES/PBT)
**성격**: 비기능 요구 확정 + 기술 스택 결정

`[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 산출물을 생성합니다.

---

## A. 실행 체크리스트

- [x] `nfr-requirements.md` — 확장성·성능·가용성·보안·신뢰성·유지보수성 NFR
- [x] `tech-stack-decisions.md` — 기술 스택 확정·근거
- [x] 확장 규칙(SEC/RES/PBT) NFR 매핑
- [x] 이미 확정된 상위 결정(FastAPI/PostgreSQL/docker-compose/demo scale) 정합성 확인

---

## B. 기 확정 사항 (상위 단계 승계)
- 백엔드=Python FastAPI, DB=PostgreSQL, 배포=로컬 docker-compose, 규모=small/demo(매장당 수~수십 테이블)
- 인증=관리자 JWT 16h(쿠키)/고객 세션 토큰, 실시간=인메모리 이벤트 버스+SSE
- DR=Backup & Restore(hours RTO/RPO)

---

## C. 질문 (NFR Questions)

## Question 1: 성능 목표(응답시간)
API 응답시간 목표를 어떻게 설정할까요?

A) 일반 API p95 < 300ms, SSE 신규 주문 반영 < 2s (요구사항 부합, demo 적정) (권장)

B) 더 엄격 (p95 < 100ms)

C) 목표 미설정(베스트 에포트)

X) Other

[Answer]: A

## Question 2: 동시성/부하 목표
동시 처리 목표를 어떻게 잡을까요?

A) 매장당 동시 수십 세션, 단일 인스턴스로 충분(demo) — 커넥션 풀 기본값 (권장)

B) 수백 동시 세션 대비(풀 튜닝·부하테스트 포함)

X) Other

[Answer]: A

## Question 3: 가용성 목표
가용성/복구 목표를 어떻게 설정할까요?

A) 단일 인스턴스, best-effort 가용성 + Backup & Restore(hours RTO/RPO), 헬스체크 기반 재기동 (demo 부합, 권장)

B) 다중 인스턴스 HA

X) Other

[Answer]: A

## Question 4: 테스트 커버리지/품질 목표 (PBT 포함)
품질/테스트 목표를 어떻게 할까요?

A) 핵심 도메인 로직 단위테스트 + 불변식 속성테스트(Hypothesis) 필수, 커버리지 권고 80%+ (권장)

B) 단위테스트만, PBT 최소

C) 커버리지 목표 미설정

X) Other

[Answer]: A

## Question 5: 관측성(Observability) 범위
관측성을 어디까지 구현할까요?

A) 구조적 로깅(상관ID) + 기본 메트릭(요청수/지연/SSE 연결) + 헬스체크 (RES-05, demo 적정) (권장)

B) 로깅만

C) 풀 스택(분산 트레이싱·대시보드 포함)

X) Other

[Answer]: A

## Question 6: 비밀/설정 관리
비밀(JWT 시크릿, DB 비번)·설정을 어떻게 관리할까요?

A) 환경변수(.env, docker-compose) + 예시 파일(.env.example), 시크릿 커밋 금지 (demo 적정, 권장)

B) 시크릿 매니저(Vault 등)

X) Other

[Answer]: A

## Question 7: 데이터 보호(전송/저장)
데이터 보호 수준을 어떻게 할까요?

A) 비밀번호 bcrypt, 토큰 서명 검증, 로컬은 HTTP(문서에 프로덕션 HTTPS/HSTS 권고 명시) (demo 적정, 권장)

B) 로컬도 TLS 강제(자체 서명 인증서)

X) Other

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 모호성/모순을 점검하고 산출물을 생성합니다.
