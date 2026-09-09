# Code Generation Summary — U1 backend-core

**단계**: CONSTRUCTION → Code Generation (Part 2 완료)
**프로젝트**: Greenfield 모노레포, 모듈러 모놀리스
**검증**: `pytest` — **14 passed** (Hypothesis 속성 테스트 포함), 전 파일 `py_compile` OK

이 단위는 횡단 기반(core 인프라 + shared 도메인 모델)을 제공하며, U2–U6가 이를 승계한다.

---

## 생성 파일 목록 (Created)

### 프로젝트 루트 / 설정
| 경로 | 설명 |
|------|------|
| `backend/pyproject.toml` | 의존성·pytest·coverage 설정 |
| `backend/.env.example` | 환경변수 예시(.env 비커밋) `[SEC-01]` |
| `backend/.gitignore` | 시크릿·산출물 제외 |
| `backend/README.md` | 실행·테스트·마이그레이션 가이드 |
| `docker-compose.yml` (루트) | db/backend/backup 서비스 스택 |

### app/core (횡단 인프라)
| 경로 | 설명 | 확장 |
|------|------|------|
| `app/core/config.py` | pydantic-settings 설정 | SEC-01 |
| `app/core/database.py` | SQLAlchemy 엔진/세션/풀/트랜잭션 | NFR-S2, RES-10 |
| `app/core/context.py` | TenantContext(ContextVar) | SEC-08 |
| `app/core/logging.py` | 구조적 JSON 로그 + 마스킹 | SEC-03 |
| `app/core/errors.py` | 도메인 오류 + 중앙 예외 핸들러(fail-closed) | SEC-03/15 |
| `app/core/notifier.py` | Notifier 인터페이스 + LogNotifier | SEC-14, RES-15 |
| `app/core/ratelimit.py` | 인메모리 슬라이딩 윈도우 레이트리밋 | SEC-11 |
| `app/core/middleware.py` | 상관ID + 보안 헤더 미들웨어 | SEC-04 |
| `app/core/events.py` | 인메모리 EventBus(pub/sub) | NFR-P2 |
| `app/core/health.py` | /health·/health/deep·/metrics | RES-06 |
| `app/core/metrics.py` | 요청/지연/오류/SSE 카운터 | RES-05 |

### app/shared (공용 도메인)
| 경로 | 설명 | 확장 |
|------|------|------|
| `app/shared/models.py` | 6 엔티티(Store/Menu/Table/TableSession/Order/OrderHistory), UUID PK, soft-delete, store_id, 복합/부분유니크 인덱스 | BR-C10/11, SEC-13 |
| `app/shared/repository.py` | TenantScopedRepository(store_id 강제 + 소유권) | SEC-08, PBT-03 |
| `app/shared/schemas.py` | 공통 Pydantic 스키마(에러/헬스/페이지) | — |
| `app/main.py` | FastAPI 앱 팩토리(미들웨어·핸들러·헬스 라우터·lifespan) | SEC-04/08, RES-07 |

### tests (생성만, 실행은 Build & Test)
| 경로 | 설명 | 확장 |
|------|------|------|
| `tests/conftest.py` | 격리된 in-memory DB 픽스처 | PBT-06 |
| `tests/test_tenant_isolation.py` | **Hypothesis 속성 테스트** — 교차 테넌트 격리 불변식 | PBT-03 |
| `tests/test_repository.py` | 스탬핑·소프트삭제·소유권 | SEC-08/13 |
| `tests/test_logging_masking.py` | 민감정보 마스킹(속성 포함) | SEC-03 |
| `tests/test_health.py` | 헬스·보안헤더·상관ID·메트릭 | RES-06, SEC-04 |

### 마이그레이션 / 배포
| 경로 | 설명 | 확장 |
|------|------|------|
| `backend/alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` | Alembic 설정/환경 | NFR-M2 |
| `alembic/versions/0001_initial_schema.py` | 초기 스키마(6 엔티티+인덱스+부분유니크), downgrade 지원 | RES-04 |
| `backend/Dockerfile`, `backend/entrypoint.sh` | 이미지 + 마이그레이션 후 uvicorn | RES-04 |
| `backend/scripts/backup.sh` | pg_dump 스케줄 백업+보존+복원안내 | RES-12 |

---

## 스토리 추적성 (완료)
| 스토리 | 구현 | 상태 |
|--------|------|:---:|
| US-TENANT-01 데이터 격리 | context.py + repository.py + models(store_id) | [x] |
| US-TENANT-02 교차 접근 차단 | repository.py(빈결과/404 일반화) + errors.py | [x] |
| US-TENANT-03 로깅/마스킹 | logging.py + middleware.py | [x] |
| US-TENANT-04 헬스/백업 | health.py + backup.sh + compose | [x] |
| US-TENANT-05 보안 알림 | notifier.py | [x] |

---

## 확장 규칙 준수 요약 (U1 Code Generation)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ | 미들웨어(SEC-04)·컨텍스트/격리(SEC-08)·마스킹(SEC-03)·레이트리밋(SEC-11)·예외 fail-closed(SEC-15)·.env(SEC-01)·bcrypt 필드(SEC-02) |
| PBT | ✅ | Hypothesis 격리 불변식·마스킹 속성 테스트 통과(14 passed) → PBT-03/06 |
| Resiliency | ✅ | 트랜잭션(RES-10)·헬스(RES-06)·이벤트버스·백업(RES-12)·Alembic 롤백(RES-04)·graceful lifespan(RES-07) |

---

## 실행 방법
```bash
cp backend/.env.example backend/.env   # 시크릿 설정
docker compose up -d --build            # http://localhost:8000/docs
# 테스트: cd backend && pip install -e ".[dev]" && pytest   → 14 passed
```
