# Infrastructure Design 계획 — U1 backend-core

**단계**: CONSTRUCTION → Infrastructure Design (Part 1: Planning)
**단위**: U1 backend-core (횡단 인프라 — 전체 스택 공유)
**입력**: U1 functional-design, nfr-design(logical-components.md), tech-stack-decisions.md
**성격**: 논리 컴포넌트 → 실제 인프라 서비스 매핑 (로컬 docker-compose 중심)

`[Answer]:` 태그를 채운 뒤 알려주시면, 모호성을 점검하고 산출물을 생성합니다.

---

## A. 실행 체크리스트

- [x] `infrastructure-design.md` — 컴포넌트→인프라 매핑
- [x] `deployment-architecture.md` — docker-compose 배포 아키텍처(+다이어그램)
- [x] `shared-infrastructure.md` (횡단 공유 인프라) — 전체 단위 공유
- [x] 확장 규칙(SEC/RES/PBT) 인프라 매핑

---

## B. 기 확정 사항 (승계)
- 로컬 docker-compose, 단일 인스턴스·단일 리전(RES-08), PostgreSQL 16, FastAPI/Uvicorn
- 인메모리 이벤트버스+SSE, pg_dump 백업, 헬스체크, .env 설정, 이미지 태그 배포+Alembic 롤백(RES-04)

---

## C. 질문 (Infrastructure Design Questions)

## Question 1: 배포 환경 (Deployment Environment)
배포 대상 환경을 어떻게 확정할까요?

A) 로컬 docker-compose 단일 환경(개발=demo). 클라우드 미사용, 향후 이전 경로만 문서화 (요구사항 Q5=A, 권장)

B) 로컬 + 클라우드(AWS 등) 동시 대상

X) Other

[Answer]: A

## Question 2: 컴퓨트 (Compute)
백엔드 실행 방식을 어떻게 할까요?

A) 단일 컨테이너(uvicorn), compose 서비스로 구동, 리소스 제한은 compose 설정 (권장)

B) 다중 워커/gunicorn+uvicorn workers

X) Other

[Answer]: A

## Question 3: 스토리지 (Storage)
DB·백업 스토리지를 어떻게 구성할까요?

A) PostgreSQL 컨테이너 + 명명된 볼륨(named volume) 영속화, pg_dump 백업을 별도 볼륨/호스트 경로에 저장 (권장)

B) 관리형 DB(RDS 등)

X) Other

[Answer]: A

## Question 4: 메시징 (Messaging)
이벤트/비동기 처리를 어떻게 할까요?

A) 인메모리 이벤트버스(외부 브로커 없음, demo). 확장 시 Redis pub/sub 경로 문서화 (권장)

B) 지금부터 Redis/RabbitMQ 도입

X) Other

[Answer]: A

## Question 5: 네트워킹 (Networking)
네트워크/라우팅을 어떻게 구성할까요?

A) compose 내부 네트워크 + 백엔드 포트 노출, 프론트(U5/U6)는 별도 서비스로 API 호출. LB/게이트웨이 미도입(문서화) (권장)

B) Nginx 리버스 프록시/게이트웨이 도입

X) Other

[Answer]: A

## Question 6: 모니터링 (Monitoring)
관측성 인프라를 어떻게 구성할까요?

A) 애플리케이션 구조적 로그(stdout→compose logs) + /health·/metrics 엔드포인트. 외부 모니터링 스택 미도입(문서화) (권장)

B) Prometheus+Grafana 스택 도입

X) Other

[Answer]: A

## Question 7: 공유 인프라·멀티테넌시 (Shared Infra)
멀티테넌시 리소스 격리를 인프라 수준에서 어떻게 할까요?

A) 단일 DB·shared-schema + store_id 논리 격리(Application Design Q4 승계), 인프라는 전체 단위가 공유 (권장)

B) 테넌트별 스키마/DB 분리

X) Other

[Answer]: A

---

**모든 `[Answer]:` 태그를 채운 뒤 알려주시면**, 모호성/모순을 점검하고 산출물을 생성합니다.
