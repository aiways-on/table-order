# NFR Requirements — U1 backend-core

**단계**: CONSTRUCTION → NFR Requirements
**단위**: U1 backend-core (횡단 기반)
**규모 전제**: small/demo (매장당 수~수십 테이블), 로컬 docker-compose, 단일 인스턴스
**결정**: 계획 질문 Q1–Q7 모두 A

각 NFR에 측정 지표(Metric)·목표(Target)·확장 매핑을 명시한다. U1이 정의하는 횡단 NFR은 이후 모든 단위(U2–U6)에 적용된다.

---

## 1. 성능 (Performance) — Q1=A
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-P1 | 일반 REST API 응답시간 | p95 < 300ms, p99 < 600ms (로컬/demo 부하 기준) | — |
| NFR-P2 | SSE 신규 주문 이벤트 전달 지연 | 발생 → 관리자/고객 화면 반영 < 2s (US-ORDER-09) | RES-06 |
| NFR-P3 | DB 쿼리 | 인덱스 사용(테넌트 스코프 복합 인덱스), N+1 회피 | — |
| NFR-P4 | 헬스체크 응답 | shallow < 50ms | RES-06 |

## 2. 확장성/동시성 (Scalability & Concurrency) — Q2=A
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-S1 | 동시 세션 | 매장당 동시 수십 세션(전체 demo 규모)을 단일 인스턴스로 처리 | — |
| NFR-S2 | DB 커넥션 풀 | SQLAlchemy 풀 기본값(pool_size≈5, max_overflow≈10), 환경변수로 조정 가능 | — |
| NFR-S3 | SSE 연결 | 인메모리 이벤트 버스로 브로드캐스트, 연결당 경량 큐 | — |
| NFR-S4 | 수평 확장 | demo 범위 밖(단일 인스턴스). 향후 확장 시 이벤트 버스 외부화 필요 — 문서화 | RES-08(NFR Design) |

## 3. 가용성/복구 (Availability & Recovery) — Q3=A
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-A1 | 가용성 | 단일 인스턴스 best-effort(공식 SLA 없음, demo) | — |
| NFR-A2 | 복구 전략 | Backup & Restore | RES-02 |
| NFR-A3 | RTO | hours (수 시간 내 복원) | RES-02 |
| NFR-A4 | RPO | hours (마지막 스케줄 백업 시점) | RES-02, RES-12 |
| NFR-A5 | 재기동 | 헬스체크 실패 시 컨테이너 재시작(docker restart policy) | RES-06 |
| NFR-A6 | 우아한 종료 | SIGTERM 시 진행 중 요청 마무리·SSE 연결 정리 | RES-07 |

## 4. 신뢰성/복원력 (Reliability & Resiliency)
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-R1 | 오류 처리 | fail-closed 기본, 일반화 오류 응답(내부 정보 비노출) | SEC-15 |
| NFR-R2 | 타임아웃 | DB/외부 호출에 타임아웃 설정 | RES-09 |
| NFR-R3 | 트랜잭션 | 주문/세션 상태 전이는 원자적(트랜잭션 경계 명확) | RES-10 |
| NFR-R4 | 백업 자동화 | 스케줄 pg_dump + 보존 정책, 복원 절차 문서화 | RES-12 |

## 5. 보안 (Security)
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-SE1 | 비밀번호 저장 | bcrypt(cost factor 12), 평문 저장 금지 | SEC-02 |
| NFR-SE2 | 관리자 토큰 | JWT 서명검증, 만료 16h, HttpOnly+Secure 쿠키 | SEC-08 |
| NFR-SE3 | 고객 세션 토큰 | 서버 검증, 세션 종료 시 무효화 | SEC-08 |
| NFR-SE4 | 로그인 레이트리밋 | 계정/IP당 시도 제한(예: 5회/분 후 지연·차단) | SEC-11 |
| NFR-SE5 | 입력 검증·파라미터라이즈드 쿼리 | 모든 입력 검증, ORM 파라미터 바인딩 | SEC-05 |
| NFR-SE6 | 보안 헤더·CORS | CSP/HSTS/XCTO/XFO/Referrer-Policy, 명시적 오리진 | SEC-04 |
| NFR-SE7 | 민감정보 마스킹 | password/token/hash 로깅 금지 | SEC-03 |
| NFR-SE8 | 데이터 보호(전송) | 로컬 HTTP 허용, 프로덕션 HTTPS/HSTS 강제 — 문서 권고(Q7=A) | SEC-04 |

## 6. 관측성 (Observability) — Q5=A
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-O1 | 구조적 로깅 | JSON 로그, correlation_id 전파 | SEC-03, RES-05 |
| NFR-O2 | 메트릭 | 요청 수·지연·오류율·SSE 활성 연결 수 노출(/metrics 또는 로그) | RES-05 |
| NFR-O3 | 헬스체크 | shallow(/health), deep(/health/deep, DB 확인) | RES-06 |
| NFR-O4 | 보안 이벤트 | SECURITY 레벨 기록 + notifier 어댑터 호출 | SEC-14, RES-15 |

## 7. 유지보수성 (Maintainability)
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-M1 | 모듈 경계 | 도메인 모듈별 router/service/repository/schemas 분리 | — |
| NFR-M2 | 마이그레이션 | Alembic 버전 관리, 자동 스키마 변경 추적 | — |
| NFR-M3 | 설정 관리 | 환경변수(.env) + .env.example, 시크릿 커밋 금지(Q6=A) | SEC-01 |
| NFR-M4 | 코드 품질 | 타입 힌트, lint/format 표준 | — |

## 8. 품질/테스트 (Quality & Testability) — Q4=A
| ID | 요구 | 목표 | 확장 |
|----|------|------|------|
| NFR-T1 | 단위 테스트 | 핵심 도메인 로직 커버, 권고 커버리지 80%+ | — |
| NFR-T2 | 속성 기반 테스트 | Hypothesis로 불변식 검증(테넌트 격리·검증·집계) | PBT-01~10 |
| NFR-T3 | 테스트 격리 | 테스트 DB 분리, 픽스처 기반 셋업/티어다운 | PBT-06 |

---

## 확장 규칙 준수 요약 (U1 NFR Requirements)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ 준수 | NFR-SE1~8(bcrypt/JWT/레이트리밋/검증/헤더/마스킹/전송보호), NFR-M3(설정) → SEC-01~05/08/11/14 |
| PBT | ✅ 준수 | NFR-T1~T3(단위+Hypothesis 속성테스트, 격리) → PBT-01~10 (구현은 Code Gen) |
| Resiliency | ✅ 준수 | NFR-A2~A6(Backup&Restore/RTO·RPO/재기동/우아한종료), NFR-R1~R4, NFR-O1~O4 → RES-02/05/06/07/09/10/12/15 |

**비차단(NFR Design에서 확정)**: RES-04(CI/CD·롤백), RES-08(리전 토폴로지·수평확장), RES-14(복원력 테스트).
