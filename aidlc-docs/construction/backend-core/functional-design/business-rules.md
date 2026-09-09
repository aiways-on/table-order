# Business Rules — U1 backend-core

**단계**: CONSTRUCTION → Functional Design
**형식**: BR-{번호}. 각 규칙에 확장 태그·검증(불변식) 표기.

---

## 테넌트 격리 (Tenant Isolation)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C01 | 모든 테넌트 엔티티 접근은 컨텍스트의 store_id로 스코프한다. | SEC-08 |
| BR-C02 | 다른 store_id 리소스에 대한 조회/변경은 거부(403 또는 빈 결과)한다. 객체 존재 여부를 노출하지 않는다. | SEC-08, SEC-15 |
| BR-C03 | 격리 불변식: 임의의 (컨텍스트 store, 타 store 리소스) 조합에서 교차 접근이 성공하지 않는다. | PBT-03 |
| BR-C04 | 격리는 Repository에서 강제하고 서비스에서 소유권을 재확인한다(이중 방어). | SEC-08 |

## 인가 (Authorization)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C05 | 관리자 전용 작업은 role=admin 컨텍스트에서만 허용한다. | SEC-08 |
| BR-C06 | 고객 컨텍스트는 자기 store+table+session 범위로만 제한된다. | SEC-08 |

## 입력 검증 (Validation)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C07 | 모든 입력은 타입·길이·형식 검증을 통과해야 하며 위반 시 거부한다. | SEC-05 |
| BR-C08 | DB 접근은 파라미터라이즈드(ORM)만 사용한다(문자열 결합 금지). | SEC-05 |
| BR-C09 | 검증 규칙은 도메인 불변식과 일치한다(price≥0, qty≥1, items 비어있지 않음, image_url은 URL 형식). | PBT-03, PBT-07 |

## 식별자·시간 (Identity & Time)
| ID | 규칙 |
|----|------|
| BR-C10 | 모든 엔티티 PK는 UUID(v4)를 사용한다. |
| BR-C11 | 모든 시간 값은 UTC(timezone-aware)로 저장하며 표시 계층에서 로컬로 변환한다. |

## 삭제 (Deletion)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C12 | 주문·메뉴 삭제는 소프트 삭제(deleted_at)로 수행한다. | SEC-13 |
| BR-C13 | 삭제된 레코드는 일반 조회·집계(총액 등)에서 제외한다. | PBT-03 |

## 오류 처리 (Error Handling)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C14 | 인증·인가 실패는 내부 사유를 노출하지 않는 일반화 메시지로 응답한다. | SEC-15 |
| BR-C15 | 불확실한 상태에서는 거부(fail-closed)를 기본으로 한다. | SEC-15 |
| BR-C16 | 예기치 않은 예외는 상관ID를 포함한 일반 메시지로 응답하고 스택/내부 정보를 노출하지 않는다. | SEC-03, SEC-15 |

## 로깅·알림 (Logging & Notification)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C17 | 로그는 timestamp(UTC)·correlation_id·level·message·context를 포함한다. | SEC-03 |
| BR-C18 | password/token/session_token/hash 등 민감정보는 로깅하지 않거나 마스킹한다. | SEC-03 |
| BR-C19 | 보안 이벤트(로그인 실패, 인가 거부, 직권 삭제)는 SECURITY 레벨로 기록하고 알림 어댑터를 호출한다. | SEC-14, RES-15 |
| BR-C20 | 알림 어댑터는 인터페이스로 정의하고 기본 구현은 로그 기록으로 한다(실제 채널 추후 연결). | RES-15 |

## 보안 헤더·CORS
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C21 | 응답에 CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy를 설정한다. | SEC-04 |
| BR-C22 | 인증 엔드포인트 CORS는 명시적 허용 오리진만 허용한다(와일드카드 금지). | SEC-08 |

## 복원력 (Resiliency)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-C23 | shallow(/health)·deep(/health/deep, DB 확인) 헬스체크를 제공한다. | RES-06 |
| BR-C24 | 영속 데이터는 스케줄된 pg_dump로 백업하고(암호화·보존 정책) 복원 절차를 문서화한다. | RES-12, RES-02 |

---

## 확장 규칙 준수 요약 (U1 Functional Design)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ 준수 | BR-C01·02·04·05·06(격리/인가), C07·08·09(검증), C12·13(삭제), C14~16(오류), C17~22(로깅/헤더) → SEC-03/04/05/08/12/13/14/15 |
| PBT | ✅ 준수 | BR-C03(격리 불변식), C09/C13(검증·집계 불변식) → PBT-03/07 (테스트는 Code Gen) |
| Resiliency | ✅ 준수 | BR-C19/C20(알림 RES-15), BR-C23(RES-06), BR-C24(RES-12/02) |

**비차단**: RES-04(CI/CD·롤백)/RES-08(리전 토폴로지)/RES-14(복원력 테스트)는 NFR Design에서 확정 예정.
