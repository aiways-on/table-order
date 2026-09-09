# NFR Design 계획 — U1 backend-core

**단계**: CONSTRUCTION → NFR Design (Part 1: Planning)
**단위**: U1 backend-core
**입력**: U1 `nfr-requirements.md`, `tech-stack-decisions.md`, 확장(SEC/RES/PBT)
**성격**: NFR을 설계 패턴·논리적 컴포넌트로 구체화 (여기서 RES-04/08/14 확정)

`[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 산출물을 생성합니다.

---

## A. 실행 체크리스트

- [x] `nfr-design-patterns.md` — 복원력·성능·확장·보안 설계 패턴
- [x] `logical-components.md` — 미들웨어·이벤트버스·백업·헬스 등 논리 컴포넌트
- [x] 보류 항목 확정: RES-04(변경관리·롤백), RES-08(리전 토폴로지), RES-14(복원력 테스트)
- [x] 확장 규칙(SEC/RES/PBT) 패턴 매핑

---

## B. 기 확정 사항 (승계)
- p95<300ms/SSE<2s, 단일 인스턴스 수십 세션, Backup&Restore(hours RTO/RPO)
- 인메모리 이벤트버스+SSE, 구조적 로깅+메트릭+헬스, .env 설정, bcrypt/JWT/레이트리밋

---

## C. 질문 (NFR Design Questions)

## Question 1: 복원력 패턴 (Resilience)
DB/외부 호출 실패 대응 패턴을 어떻게 할까요?

A) 타임아웃 + 제한적 재시도(지수 백오프, 멱등 연산 한정) + fail-closed, DB 다운 시 deep health 실패 처리 (demo 적정, 권장)

B) 서킷 브레이커 등 본격 패턴 도입

C) 재시도 없음(단순 실패 전파)

X) Other

[Answer]: A

## Question 2: 성능 패턴 (Performance)
성능 최적화 전략을 어떻게 할까요?

A) 테넌트 스코프 복합 인덱스 + 커넥션 풀 + 페이지네이션, 캐시는 미도입(demo 규모) (권장)

B) 애플리케이션 캐시(예: 메뉴 조회) 도입

C) 최적화 없음(베스트 에포트)

X) Other

[Answer]: A

## Question 3: 확장 패턴 (Scalability) — RES-08 확정
수평 확장/리전 토폴로지를 어떻게 결정할까요?

A) 단일 인스턴스·단일 리전(demo 범위), 향후 확장 시 이벤트버스 외부화(Redis pub/sub)·무상태화 경로만 문서화 (권장)

B) 지금부터 다중 인스턴스 대비(외부 이벤트버스 즉시 도입)

X) Other

[Answer]: A

## Question 4: 보안 패턴 (Security)
보안 구현 패턴을 어떻게 배치할까요?

A) 미들웨어 계층화(상관ID→인증→인가→레이트리밋→보안헤더) + 중앙 예외 핸들러(fail-closed) + 입력검증(Pydantic) (권장)

B) 각 라우트에서 개별 처리

X) Other

[Answer]: A

## Question 5: 변경관리·롤백 (RES-04 확정)
CI/CD·배포 롤백 전략을 어떻게 할까요?

A) docker-compose 이미지 태그 기반 배포 + 이전 태그 롤백 + Alembic downgrade 마이그레이션 롤백, 절차 문서화 (demo 적정, 권장)

B) 본격 CI/CD 파이프라인(블루-그린/카나리)

C) 수동 배포만(롤백 절차 없음)

X) Other

[Answer]: A

## Question 6: 복원력 테스트 (RES-14 확정)
복원력 테스트를 어떻게 포함할까요?

A) 백업→복원 리허설 절차 + DB 다운 시 헬스/오류 동작 테스트 + 우아한 종료 테스트를 테스트 계획에 포함 (권장)

B) 카오스 엔지니어링 도구 도입

C) 복원력 테스트 없음

X) Other

[Answer]: A

## Question 7: 논리 컴포넌트 구성 (Logical Components)
횡단 논리 컴포넌트를 어떻게 배치할까요?

A) core에 집약: Settings, DB 세션 팩토리, 미들웨어 스택, EventBus(pub/sub), Logger, HealthService, BackupScript, Notifier 인터페이스 (권장)

B) 다른 구성 — [Answer]에 명시

X) Other

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 모호성/모순을 점검하고 산출물을 생성합니다.
