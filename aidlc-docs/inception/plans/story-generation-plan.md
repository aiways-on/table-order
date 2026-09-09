# User Stories 생성 계획 (Story Generation Plan)

**단계**: INCEPTION → User Stories (Part 1: Planning)
**역할**: Product Owner
**입력**: `aidlc-docs/inception/requirements/requirements.md`

이 문서는 (1) 사용자 스토리 생성 방법론/체크리스트와 (2) 방향 결정을 위한 질문을 담고 있습니다.
아래 **"질문"** 섹션의 각 `[Answer]:` 태그를 채운 뒤 "완료"라고 알려주시면, 계획을 확정하고 승인 후 스토리를 생성합니다.

---

## A. 스토리 생성 실행 체크리스트 (승인 후 Part 2에서 수행)

- [x] 확정된 페르소나 목록을 `personas.md`로 생성 (아키타입, 목표, 특성, 페인포인트)
- [x] 요구사항의 각 기능(FR-C1~5, FR-A1~4, FR-MT1~2)을 사용자 스토리로 변환
- [x] 각 스토리를 INVEST 기준(Independent, Negotiable, Valuable, Estimable, Small, Testable)에 맞게 작성
- [x] 각 스토리에 수용 기준(Acceptance Criteria) 포함
- [x] 각 스토리를 관련 페르소나에 매핑
- [x] 활성 확장 연계 표기: 보안/복원력/PBT 관련 수용 기준 또는 참조 태깅 (예: 인증 스토리 ↔ SECURITY-12, 세션 불변식 ↔ PBT-03)
- [x] 스토리를 승인된 분류 방식(아래 질문 Q2)으로 그룹화/정리
- [x] `stories.md` 생성 및 `aidlc-state.md` 갱신

---

## B. 스토리 분류 방식 옵션 (질문 Q2에서 선택)

- **User Journey-Based**: 사용자 워크플로우/여정 흐름을 따라 스토리 구성 (예: 고객 착석→메뉴→주문→내역)
- **Feature-Based**: 시스템 기능/역량 단위로 구성 (인증, 메뉴관리, 주문, 세션관리…)
- **Persona-Based**: 페르소나(고객/관리자)별로 그룹화
- **Domain-Based**: 비즈니스 도메인 단위 (인증/메뉴/주문/세션·이력)
- **Epic-Based**: 상위 Epic 아래 하위 스토리 계층 구조
- **Hybrid**: 예) Epic(도메인) → Persona별 여정 스토리 (권장 후보)

트레이드오프: Journey는 UX 흐름 이해에 강하나 기능 중복 가능, Feature는 구현 매핑이 쉬우나 여정 맥락 약함, Persona는 이해관계자 정렬에 강함, Epic-Hybrid는 구조적이나 초기 오버헤드.

---

## C. 질문 (Planning Questions)

## Question 1: 페르소나 범위
어떤 사용자 페르소나를 정의할까요?

A) 2개 핵심 페르소나 — 고객(주문자) + 매장 관리자/운영자

B) 3개 — 고객 + 매장 관리자 + 매장 직원/서버(주문 상태 변경 등 현장 운영 담당 별도)

C) 4개 — 고객 + 매장 관리자(설정/메뉴) + 홀 직원(주문 모니터링) + (선택) 슈퍼관리자(멀티매장 총괄)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: 스토리 분류 방식
스토리를 어떤 방식으로 구성할까요? (섹션 B 참고)

A) Hybrid — Epic(도메인: 인증/메뉴/주문/세션·이력) 아래 페르소나별 여정 스토리 (권장)

B) Persona-Based — 고객/관리자별로 그룹화

C) Feature-Based — 시스템 기능 단위

D) User Journey-Based — 사용자 여정 흐름 단위

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: 스토리 세분화(Granularity)
스토리 크기/상세 수준은 어느 정도로 할까요?

A) 세분화(작게) — 기능을 여러 작은 스토리로 분할, 스토리 수 많음 (스프린트 친화적)

B) 중간 — 기능 단위(FR)당 1~2개 스토리 수준 (권장, MVP 균형)

C) 큰 단위 — Epic 위주, 상위 수준 스토리 소수

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: 수용 기준(Acceptance Criteria) 형식
수용 기준을 어떤 형식으로 작성할까요?

A) Gherkin 스타일 (Given/When/Then) — 테스트 자동화·PBT 연계에 유리 (권장)

B) 체크리스트/불릿 형식 — 간결한 조건 목록

C) 혼합 — 핵심 시나리오는 Given/When/Then, 부가 조건은 불릿

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5: 비확장 관련 스토리 포함 범위
활성 확장(보안/복원력/PBT)의 요구를 스토리에 어떻게 반영할까요?

A) 각 관련 스토리의 수용 기준에 확장 규칙을 인라인으로 반영 (예: 로그인 스토리에 브루트포스 방지·bcrypt 조건 포함) (권장)

B) 별도의 비기능/기술 스토리(NFR 스토리)로 분리하여 관리

C) 혼합 — 기능 스토리에 인라인 + 횡단 관심사(로깅/관측성 등)는 별도 기술 스토리

X) Other (please describe after [Answer]: tag below)

[Answer]: A
