# Auth & Session Business Rules — U2 auth-session

**형식**: BR-A{번호}. 확장 태그·불변식 표기.

---

## 관리자 인증
| ID | 규칙 | 확장 |
|----|------|------|
| BR-A01 | 관리자 로그인은 store_code + admin_username + password 조합으로 인증한다. | SEC-05 |
| BR-A02 | 비밀번호는 bcrypt(cost 12)로 해싱 저장하며 평문 저장·로깅을 금지한다. | SEC-12, SEC-03 |
| BR-A03 | 자격 증명 실패는 사유를 노출하지 않는 일반화 오류로 응답한다(fail-closed). | SEC-15 |
| BR-A04 | 성공 시 JWT(sub=store_id, role=admin, exp=16h, iss)를 발급한다. | SEC-08 |
| BR-A05 | 관리자 세션 쿠키는 HttpOnly·Secure·SameSite=Strict, Max-Age=16h. | SEC-12 |
| BR-A06 | 매 요청 JWT의 서명·만료·발급자를 서버에서 검증한다. 실패 시 401. | SEC-08 |
| BR-A07 | 로그아웃은 쿠키 삭제로 처리한다(단기 만료로 위험 제한, 블랙리스트 없음). | — |

## 로그인 시도 제한
| ID | 규칙 | 확장 |
|----|------|------|
| BR-A08 | 로그인 실패는 계정+IP 키로 슬라이딩 윈도우 제한(기본 5회/60s)한다. 초과 시 429. | SEC-12 |
| BR-A09 | 모든 인증 실패는 SECURITY 이벤트로 기록하고 Notifier를 호출한다. | SEC-14 |
| BR-A10 | 로그인 성공 시 해당 키의 시도 카운트를 리셋한다. | — |

## 테이블/세션 인증
| ID | 규칙 | 확장 |
|----|------|------|
| BR-A11 | 테이블 초기설정은 관리자 컨텍스트에서만 허용한다(role=admin). | SEC-08 |
| BR-A12 | table_password는 bcrypt로 해싱 저장한다. | SEC-12 |
| BR-A13 | 세션 토큰은 암호학적 난수(secrets, ≥32B urlsafe)로 발급하고 DB에 저장한다. | SEC-12 |
| BR-A14 | 테이블당 status=active 세션은 최대 1개(부분유니크 인덱스). 재개 시 기존 active 재사용. | — |
| BR-A15 | 세션 토큰 검증은 status=active && 미만료(16h)를 요구한다. | SEC-08 |
| BR-A16 | 고객 세션 컨텍스트는 자기 store+table+session 범위로만 스코프된다. | SEC-08 |
| BR-A17 | 세션 종료 시 status=closed·closed_at 설정으로 토큰을 즉시 무효화한다. | — |

## 검증 불변식 (PBT 대상)
| ID | 규칙 | 확장 |
|----|------|------|
| BR-A18 | 임의 비밀번호에 대해 bcrypt 해시는 원문과 다르며 verify는 정확한 원문에만 참이다. | PBT-07 |
| BR-A19 | 만료·close된 세션 토큰은 어떤 입력에서도 검증에 성공하지 않는다. | PBT-03 |
| BR-A20 | 발급된 JWT는 서버 검증 시 동일 store_id/role을 복원하고, 변조 토큰은 거부된다. | PBT-07 |

---

## 확장 규칙 준수 요약 (U2 Functional Design)
| 확장 | 판정 | 근거 |
|------|:---:|------|
| Security | ✅ | BR-A01~A17 (bcrypt·JWT·쿠키·레이트리밋·세션 스코프) → SEC-03/05/08/12/14/15 |
| PBT | ✅ | BR-A18~A20 불변식(해시/세션/JWT) → PBT-03/07 (테스트 Code Gen) |
| Resiliency | ✅ | fail-closed(BR-A03), 세션 무효화(BR-A17), 보안 이벤트 알림(BR-A09) → U1 RES 패턴 승계 |
