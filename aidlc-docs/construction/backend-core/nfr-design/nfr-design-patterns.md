# NFR Design Patterns — U1 backend-core

**단계**: CONSTRUCTION → NFR Design
**입력**: `nfr-requirements.md`, `tech-stack-decisions.md`
**결정**: 질문 Q1–Q7 모두 A. 여기서 RES-04/08/14 확정.

NFR을 구체적 설계 패턴으로 매핑한다. 모든 패턴은 U1 core에 구현되어 U2–U6에 적용된다.

---

## 1. 복원력 패턴 (Resilience) — Q1=A
| 패턴 | 설계 | 매핑 |
|------|------|------|
| Timeout | DB 세션·쿼리·외부 호출에 타임아웃(기본 5s, env 조정) | NFR-R2, RES-09 |
| Bounded Retry | 멱등 연산에 한해 지수 백오프 재시도(최대 2회). 비멱등(주문 생성 등)은 재시도 금지 | RES-09 |
| Fail-Closed | 불확실 상태·인가 판단 불가 시 거부 | SEC-15, NFR-R1 |
| Transactional Boundary | 상태 전이(주문/세션)는 단일 트랜잭션, 실패 시 롤백 | RES-10, NFR-R3 |
| Graceful Shutdown | SIGTERM 시 신규 수락 중단→진행 요청 마무리→SSE 연결 정리 | RES-07, NFR-A6 |
| DB-Down Behavior | deep health가 DB 실패 감지→비정상 보고, 요청은 503 일반화 응답 | RES-06 |

> **서킷 브레이커 미도입**: 단일 인스턴스·단일 DB(demo)에서 과설계. 외부 의존성 추가 시 재검토(문서화).

## 2. 성능 패턴 (Performance) — Q2=A
| 패턴 | 설계 | 매핑 |
|------|------|------|
| Tenant-Scoped Composite Index | `(store_id, ...)` 복합 인덱스로 격리 + 조회 성능 동시 확보 | NFR-P1, NFR-P3 |
| Connection Pooling | SQLAlchemy 풀(pool_size=5, max_overflow=10) | NFR-S2 |
| Pagination | 목록 조회는 limit/offset(또는 keyset) 페이지네이션 | NFR-P1 |
| N+1 Avoidance | 관계 로딩은 selectinload/join 명시 | NFR-P3 |
| SSE Lightweight Fanout | 인메모리 버스 → 연결별 asyncio 큐 non-blocking 푸시 | NFR-P2 |

> **캐시 미도입**: demo 규모에서 DB+인덱스로 목표 충족. 메뉴 조회 등 핫패스 병목 확인 시 캐시 도입(문서화).

## 3. 확장 패턴 (Scalability) — Q3=A / **RES-08 확정**
| 항목 | 결정 |
|------|------|
| 현 토폴로지 | **단일 인스턴스·단일 리전** (demo 범위) |
| 상태성 | 인메모리 이벤트버스·레이트리밋 카운터가 인스턴스 로컬 상태 → 현재 수평 확장 불가 |
| 향후 확장 경로 (문서화만) | ① 이벤트버스를 Redis pub/sub로 외부화 ② 레이트리밋을 Redis로 이전 ③ JWT/세션 검증은 이미 무상태 ④ 로드밸런서 + N 인스턴스 |
| 리전 토폴로지 | 단일 리전. 다중 리전은 범위 밖(향후 DR 확장 시 재검토) |
| 매핑 | RES-08 (확정: 단일 리전, 확장 경로 문서화) |

## 4. 보안 패턴 (Security) — Q4=A
**미들웨어 스택(요청 처리 순서)**:
```
Request
  → [1] CorrelationId (상관ID 발급/전파)
  → [2] SecurityHeaders (응답 헤더 주입)
  → [3] Authentication (JWT 쿠키 / 세션 토큰 검증)
  → [4] Authorization (role·테넌트 컨텍스트 확립)
  → [5] RateLimit (인증 엔드포인트 등 시도 제한)
  → Router → Service → Repository
  → CentralExceptionHandler (fail-closed, 일반화 응답, 상관ID 포함)
Response
```
| 패턴 | 설계 | 매핑 |
|------|------|------|
| Layered Middleware | 횡단 관심사를 미들웨어로 중앙화 | SEC-04/08 |
| Central Exception Handler | 모든 예외를 일반화 응답으로 변환(스택 비노출) | SEC-03/15, NFR-R1 |
| Input Validation | Pydantic v2 스키마 경계 검증 | SEC-05, NFR-SE5 |
| Tenant Guard | TenantScopedRepository + 서비스 소유권 재확인(이중 방어) | SEC-08, PBT-03 |
| Secret Handling | pydantic-settings + .env, 로깅 마스킹 | SEC-01/03 |

## 5. 변경관리·롤백 (Change Mgmt) — Q5=A / **RES-04 확정**
| 항목 | 결정 |
|------|------|
| 배포 방식 | docker-compose + **이미지 태그(버전) 기반** 배포 |
| 코드 롤백 | 이전 이미지 태그로 재배포(compose up) |
| 스키마 롤백 | **Alembic downgrade** 로 마이그레이션 되돌리기 |
| 절차 문서화 | 배포/롤백 런북을 Build&Test 산출물에 포함 |
| 매핑 | RES-04 (확정: 태그 배포 + Alembic 양방향 마이그레이션 + 런북) |

> **본격 CI/CD(블루-그린/카나리) 미도입**: demo 범위 과설계. 향후 도입 경로 문서화.

## 6. 복원력 테스트 (Resiliency Testing) — Q6=A / **RES-14 확정**
| 테스트 | 내용 | 매핑 |
|--------|------|------|
| Backup/Restore Rehearsal | pg_dump 백업 → 신규 볼륨 복원 → 무결성 검증 절차 | RES-12/14 |
| DB-Down Behavior | DB 컨테이너 중단 시 deep health 실패·503 응답 확인 | RES-06/14 |
| Graceful Shutdown | SIGTERM 후 진행 요청 완료·SSE 정리 확인 | RES-07/14 |
| 배치 | Build & Test 단계 test plan에 포함(자동/수동 표기) | RES-14 |

> **카오스 엔지니어링 미도입**: demo 범위. 향후 도입 경로 문서화.

---

## 확장 규칙 준수 요약 (U1 NFR Design)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ 준수 | 미들웨어 스택(1~5)·중앙 예외핸들러·Pydantic·Tenant Guard·시크릿 → SEC-01/03/04/05/08/15 |
| PBT | ✅ 준수 | Tenant Guard 불변식·검증 패턴 명시(테스트 구현 Code Gen) → PBT-03/07 |
| Resiliency | ✅ 준수 | 타임아웃/재시도/graceful/트랜잭션/헬스 + **RES-04(롤백)·RES-08(단일리전+확장경로)·RES-14(복원력테스트) 확정** → RES-02/04/06/07/08/09/10/12/14/15 |

**보류 없음**: RES-04/08/14 모두 이 단계에서 확정 완료.
