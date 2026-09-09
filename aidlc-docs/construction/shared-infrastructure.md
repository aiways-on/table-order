# Shared Infrastructure — Table-Order (전체 단위 공유)

**정의 단위**: U1 backend-core (Infrastructure Design)
**적용 범위**: 전체 단위(U1–U6)가 공유하는 횡단 인프라
**환경**: 로컬 docker-compose 단일 환경

이 문서는 개별 단위가 재정의하지 않고 **승계**하는 공유 인프라를 규정한다.

---

## 1. 공유 인프라 자원
| 자원 | 정의 | 공유 대상 |
|------|------|-----------|
| **docker-compose 스택** | 루트 `docker-compose.yml` | 전체 |
| **`db` (PostgreSQL 16)** | 단일 DB 인스턴스, named volume `pgdata` | U1–U4(백엔드), 프론트는 API 경유 |
| **`app-net` 네트워크** | compose 내부 네트워크 | 전체 서비스 |
| **`.env` / `.env.example`** | 공유 환경변수·시크릿 관리 | 전체 |
| **`backup` 서비스** | pg_dump 스케줄, `backups` 볼륨 | DB 전체(모든 단위 데이터) |
| **관측성 규약** | stdout JSON 로그 + /health + /metrics | 전 백엔드 모듈 |

## 2. 공유 애플리케이션 인프라 (app/core, U1 제공)
| 컴포넌트 | 공유 계약 |
|----------|-----------|
| Settings | 모든 모듈이 동일 설정 소스 사용 |
| Database 세션 팩토리 | 모든 리포지토리가 공유 세션/트랜잭션 |
| MiddlewareStack | 모든 라우트에 공통 적용(상관ID/헤더/인증/인가/레이트리밋) |
| ExceptionHandler | 전역 예외 표준화 |
| EventBus | U4 order/realtime가 publish/subscribe |
| Logger/Metrics | 전 모듈 공통 |
| TenantScopedRepository | 모든 도메인 리포지토리의 베이스 |
| Notifier | 보안 이벤트 공통 알림 |

## 3. 멀티테넌시 (공유 격리 정책)
- **단일 DB · shared-schema · store_id 논리 격리** (Application Design Q4).
- 모든 테넌트 엔티티 테이블은 `store_id` 컬럼 + `(store_id, ...)` 복합 인덱스.
- 격리 강제: 애플리케이션 계층(TenantScopedRepository + 서비스 소유권 재확인, 이중 방어).
- 인프라 수준 테넌트 분리 없음(단일 공유 인프라).

## 4. 리소스 격리·공유 전략
| 항목 | 정책 |
|------|------|
| 컴퓨트 | 단일 backend 컨테이너가 전 모듈 서빙(모듈러 모놀리스) |
| 스토리지 | 단일 DB, 테이블 수준 논리 분리 |
| 네트워크 | 단일 내부 네트워크, db 내부 전용 |
| 시크릿 | 공유 .env(비커밋), 서비스별 필요한 키만 주입 |

## 5. 확장(수평) 시 공유 인프라 변경 경로 (RES-08, 문서화)
| 자원 | demo | 확장 |
|------|------|------|
| EventBus | 인메모리 | Redis pub/sub(공유) |
| RateLimit | 인메모리 | Redis(공유) |
| backend | 단일 | LB + N 인스턴스(무상태) |
| 모니터링 | logs | Prometheus/Grafana(공유) |

---

## 확장 규칙 준수 요약 (Shared Infrastructure)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ | 공유 .env 비커밋, db 내부망, 공통 미들웨어/격리(SEC-01/08) |
| PBT | N/A | 인프라 — 테스트 DB 분리는 Build&Test |
| Resiliency | ✅ | 공유 backup/health/restart, Alembic 롤백(RES-04/06/12) |
