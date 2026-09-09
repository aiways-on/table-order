# Tech Stack Decisions — U1 backend-core

**단계**: CONSTRUCTION → NFR Requirements
**범위**: 백엔드 횡단 스택(U1이 확정, U2–U6 승계). 프론트 스택은 U5/U6에서 확정.
**전제**: 상위 결정 승계 — Python/FastAPI, PostgreSQL, 로컬 docker-compose, small/demo 규모.

---

## 1. 백엔드 런타임·프레임워크
| 항목 | 결정 | 버전(권장) | 근거 |
|------|------|-----------|------|
| 언어 | Python | 3.12+ | 요구사항 Q2=A |
| 웹 프레임워크 | FastAPI | 0.11x | async, Pydantic 통합, SSE 지원, OpenAPI 자동생성 |
| ASGI 서버 | Uvicorn | 최신 안정 | FastAPI 표준, docker-compose 구동 |
| 데이터 검증 | Pydantic | v2 | 요청/응답 스키마, 입력 검증 (SEC-05) |

## 2. 데이터 계층
| 항목 | 결정 | 버전(권장) | 근거 |
|------|------|-----------|------|
| DB | PostgreSQL | 16 | Functional Design Q1=A, JSON/인덱스/동시성 |
| ORM | SQLAlchemy | 2.0 | Repository 패턴, 파라미터라이즈드 쿼리 (SEC-05) |
| 드라이버 | psycopg | 3.x | PostgreSQL 연결 |
| 마이그레이션 | Alembic | 최신 | 스키마 버전 관리 (NFR-M2) |
| 커넥션 풀 | SQLAlchemy 내장 풀 | — | pool_size=5, max_overflow=10 (env 조정) |

## 3. 인증·보안
| 항목 | 결정 | 라이브러리(권장) | 근거 |
|------|------|-----------|------|
| 비밀번호 해시 | bcrypt (cost 12) | passlib[bcrypt] | SEC-02, NFR-SE1 |
| JWT | HS256 서명 | pyjwt | 관리자 토큰 16h, SEC-08 |
| 레이트리밋 | 인메모리 카운터(demo) | slowapi 또는 자체 미들웨어 | SEC-11, NFR-SE4 |
| 보안 헤더 | 미들웨어 | 자체/secure 헤더 | SEC-04, NFR-SE6 |

## 4. 실시간
| 항목 | 결정 | 근거 |
|------|------|------|
| 실시간 방식 | SSE (Server-Sent Events) | 단방향 주문 상태 푸시에 적합, WebSocket 대비 단순 |
| 이벤트 버스 | 인메모리 pub/sub | Application Design Q2=A, demo 단일 인스턴스 |

## 5. 관측성·운영
| 항목 | 결정 | 라이브러리(권장) | 근거 |
|------|------|-----------|------|
| 로깅 | 구조적 JSON 로그 | structlog 또는 표준 logging+JSON 포매터 | SEC-03, RES-05, NFR-O1 |
| 상관ID | 요청 미들웨어 | 자체 미들웨어 | NFR-O1 |
| 헬스체크 | FastAPI 라우트 | — | RES-06, NFR-O3 |
| 설정 | pydantic-settings + .env | pydantic-settings | NFR-M3, SEC-01 |
| 백업 | pg_dump 스케줄 스크립트 | cron/컨테이너 | RES-12, NFR-R4 |

## 6. 테스트
| 항목 | 결정 | 라이브러리(권장) | 근거 |
|------|------|-----------|------|
| 테스트 러너 | pytest | pytest | 표준 |
| 속성 기반 테스트 | Hypothesis | hypothesis | PBT-01~10 (확장 요구), NFR-T2 |
| API 테스트 | httpx + FastAPI TestClient | — | 통합 테스트 |
| 커버리지 | pytest-cov | — | 권고 80%+ (NFR-T1) |

## 7. 프로젝트 구조 (승계)
```
backend/
  app/
    core/       # 설정, DB, 미들웨어, 로깅, 보안, 헬스, 이벤트버스 (U1)
    shared/     # 공용 도메인 모델, 스키마, TenantScopedRepository (U1)
    auth/       # U2
    menu/       # U3
    order/      # U4 (+session +realtime)
  alembic/
  tests/
  pyproject.toml (또는 requirements.txt)
```

---

## 결정 근거 요약
- **모든 선택은 small/demo 규모에 최적화**: 외부 인프라(메시지 브로커, 시크릿 매니저, HA) 없이 docker-compose 단일 스택으로 완결.
- **확장 규칙 준수를 위한 라이브러리는 표준·경량 우선**: passlib/pyjwt(보안), Hypothesis(PBT), Alembic(마이그레이션), structlog(관측성).
- **프로덕션 전환 지점 문서화**: HTTPS/HSTS 강제(Q7), 이벤트 버스 외부화(NFR-S4), 수평 확장(RES-08) — NFR Design/향후 과제.

## 확장 준수
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ | passlib/bcrypt, pyjwt, slowapi, pydantic 검증, 보안헤더 미들웨어 |
| PBT | ✅ | Hypothesis 채택(테스트 구현은 Code Gen) |
| Resiliency | ✅ | Alembic, pg_dump 백업, 헬스체크, 구조적 로깅, docker restart |
