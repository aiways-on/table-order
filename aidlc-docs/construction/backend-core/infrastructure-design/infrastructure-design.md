# Infrastructure Design — U1 backend-core

**단계**: CONSTRUCTION → Infrastructure Design
**결정**: 질문 Q1–Q7 모두 A. 로컬 docker-compose 단일 환경.
**입력**: nfr-design/logical-components.md, tech-stack-decisions.md

논리 컴포넌트를 실제 인프라 자원에 매핑한다. U1이 정의하는 인프라는 전체 단위(U2–U6)가 공유한다(→ `shared-infrastructure.md`).

---

## 1. 논리 컴포넌트 → 인프라 매핑
| 논리 컴포넌트 | 인프라 자원 | 비고 |
|--------------|-------------|------|
| FastAPI 앱(전 모듈) | `backend` 컨테이너 (uvicorn) | 단일 컨테이너(Q2) |
| Database | `db` 컨테이너 (postgres:16) + named volume `pgdata` | 영속화(Q3) |
| Settings | `.env` 파일 + compose `env_file`/`environment` | 시크릿 비커밋(SEC-01) |
| EventBus | 앱 프로세스 인메모리(별도 인프라 없음) | Q4 |
| Logger/Metrics | stdout → `docker compose logs` | Q6 |
| HealthService | compose `healthcheck` (/health) | RES-06 |
| BackupScript | `backup` 서비스(또는 호스트 크론) → pg_dump → `backups` 볼륨/호스트 경로 | RES-12(Q3) |
| Notifier | 앱 내 LogNotifier(기본) | SEC-14/RES-15 |
| Network | compose 내부 네트워크 `app-net` | Q5 |

## 2. 인프라 서비스 목록 (docker-compose)
| 서비스 | 이미지 | 포트 | 볼륨 | 의존 |
|--------|--------|------|------|------|
| `db` | postgres:16 | 5432(내부) | pgdata | — |
| `backend` | 자체 빌드(python:3.12-slim) | 8000 노출 | (코드) | db (healthy) |
| `backup` | postgres:16(클라이언트용) | — | backups | db |
| (`frontend-customer`) | node/nginx (U5) | 5173/80 | — | backend |
| (`frontend-admin`) | node/nginx (U6) | 5174/80 | — | backend |

> 프론트 서비스는 U5/U6에서 확정. U1은 backend/db/backup을 정의.

## 3. 컴퓨트 (Q2=A)
- 단일 uvicorn 컨테이너. 워커 수 1(demo). 리소스 제한은 compose `deploy.resources`(옵션).
- 확장 시(RES-08): 워커 증설 → 이벤트버스 외부화 필요(문서화).

## 4. 스토리지 (Q3=A)
- **운영 데이터**: `db` 컨테이너 + named volume `pgdata` (재기동 시 유지).
- **백업**: pg_dump 산출물을 `backups` 볼륨(또는 호스트 bind mount)에 보존. 보존 정책·주기 문서화(RES-12).
- 데이터 수명주기: 소프트 삭제 레코드는 DB 잔존, OrderHistory는 세션 종료 시 이관(U4).

## 5. 메시징 (Q4=A)
- 인메모리 이벤트버스. 외부 브로커 없음.
- SSE는 backend 컨테이너가 직접 스트리밍.
- 확장 교체점: Redis pub/sub(문서화, 즉시 도입 안 함).

## 6. 네트워킹 (Q5=A)
- compose 내부 네트워크 `app-net`. db는 내부 전용, backend만 호스트 포트 노출.
- LB/API 게이트웨이 미도입. 프론트는 backend API 직접 호출(CORS 명시 오리진, SEC-08).
- 확장 시: Nginx 리버스 프록시/게이트웨이 도입 경로 문서화.

## 7. 모니터링 (Q6=A)
- 구조적 JSON 로그 stdout → `docker compose logs`.
- `/health`(shallow), `/health/deep`(DB), `/metrics`(카운터) 엔드포인트.
- 외부 모니터링 스택(Prometheus/Grafana) 미도입 — 확장 경로 문서화.

## 8. 멀티테넌시·격리 (Q7=A)
- 단일 DB, **shared-schema + store_id** 논리 격리(Application Design Q4 승계).
- 인프라는 전체 단위 공유(별도 테넌트 인프라 없음).
- 격리 강제는 애플리케이션 계층(TenantScopedRepository, SEC-08/PBT-03).

---

## 확장 규칙 준수 요약 (U1 Infrastructure Design)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ | .env 시크릿 비커밋(SEC-01), db 내부 전용 네트워크, CORS 명시 오리진(SEC-08) |
| PBT | N/A | 인프라 단계 — 테스트 인프라(테스트 DB 분리)는 Build&Test에서 상세화 |
| Resiliency | ✅ | named volume 영속화, healthcheck+restart(RES-06), backup 서비스(RES-12), 이미지 태그 롤백(RES-04) |
