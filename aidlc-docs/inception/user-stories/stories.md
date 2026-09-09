# 사용자 스토리 (User Stories) — 테이블오더 서비스

**단계**: INCEPTION → User Stories (Part 2)
**구성**: Hybrid — Epic(도메인) 아래 페르소나별 스토리 / 세분화(작은 스토리) / 수용 기준 Gherkin(Given-When-Then) / 확장 규칙 인라인
**페르소나**: 고객(지민), 관리자(현우) — `personas.md` 참조
**출처**: `requirements/table-order-requirements.md`, `requirements.md`

**확장 태그 범례**: `[SEC-nn]` 보안, `[RES-nn]` 복원력, `[PBT-nn]` 속성 기반 테스트
**모든 스토리는 INVEST**(Independent·Negotiable·Valuable·Estimable·Small·Testable)를 지향.

---

# EPIC-AUTH — 인증 및 세션

## US-AUTH-01 — 관리자 매장 로그인
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 매장 식별자·사용자명·비밀번호로 로그인하기를, **so that** 내 매장 관리 화면에 안전하게 접근할 수 있다.
- **Acceptance Criteria**
  - Given 유효한 매장 식별자/사용자명/비밀번호, When 로그인을 요청하면, Then JWT가 발급되고 대시보드로 이동한다.
  - Given 잘못된 자격 증명, When 로그인을 요청하면, Then 일반화된 오류 메시지가 표시되고 로그인은 거부된다. `[SEC-15 fail-closed, 내부정보 미노출]`
  - Given 비밀번호는 저장 시, Then bcrypt로 해싱되어 저장된다(평문 저장 금지). `[SEC-12]`
- **확장 요구**: `[SEC-12]` 브루트포스 방지(연속 실패 시 잠금/지연), `[SEC-05]` 입력 검증, `[SEC-15]` 오류 처리.

## US-AUTH-02 — 관리자 세션 16시간 유지
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 로그인 세션이 16시간 유지되고 새로고침에도 살아있기를, **so that** 영업 중 반복 로그인 없이 일할 수 있다.
- **Acceptance Criteria**
  - Given 로그인된 상태, When 브라우저를 새로고침하면, Then 세션이 유지된다.
  - Given 로그인 후 16시간이 지나면, When 요청을 보내면, Then 자동 로그아웃되고 재인증을 요구한다.
  - Given 매 요청, Then JWT 서명·만료·발급자가 서버측에서 검증된다. `[SEC-08 토큰 서버측 검증]`
- **확장 요구**: `[SEC-12]` 세션 쿠키 Secure/HttpOnly/SameSite, 로그아웃 시 무효화.

## US-AUTH-03 — 관리자 로그인 시도 제한
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 반복된 로그인 실패가 차단되기를, **so that** 계정이 무차별 대입 공격으로부터 보호된다.
- **Acceptance Criteria**
  - Given N회 연속 로그인 실패, When 추가 시도를 하면, Then 잠금 또는 점진적 지연이 적용된다. `[SEC-12]`
  - Given 인증 실패 이벤트, Then 보안 이벤트로 로깅/알림 대상이 된다. `[SEC-14]`

## US-AUTH-04 — 테이블 태블릿 초기 설정(관리자 1회)
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 태블릿에 매장 식별자·테이블 번호·테이블 비밀번호를 1회 설정하기를, **so that** 이후 고객이 자동 로그인으로 즉시 주문한다.
- **Acceptance Criteria**
  - Given 관리자가 초기 설정을 입력, When 저장하면, Then 16시간 테이블 세션 설정이 생성되고 자동 로그인이 활성화된다.
  - Given 테이블 비밀번호, Then 안전하게 저장된다(해시). `[SEC-12]`
  - Given 설정 최종 로그인 정보, Then 태블릿 로컬에 저장된다.

## US-AUTH-05 — 고객 태블릿 자동 로그인
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 별도 로그인 없이 태블릿이 자동 로그인되기를, **so that** 착석 후 바로 주문할 수 있다.
- **Acceptance Criteria**
  - Given 1회 로그인 성공 이력, When 태블릿을 열면, Then 저장된 정보로 자동 로그인되어 메뉴 화면이 표시된다.
  - Given 자동 로그인 세션, Then 해당 테이블·매장 범위로만 스코프된다. `[SEC-08 객체수준 인가]`

---

# EPIC-MENU — 메뉴

## US-MENU-01 — 고객 메뉴 기본 화면 표시
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 앱을 열면 메뉴 화면이 기본으로 보이기를, **so that** 즉시 메뉴를 탐색한다.
- **Acceptance Criteria**
  - Given 자동 로그인 완료, When 화면이 로드되면, Then 메뉴 화면이 기본 화면으로 표시된다.
  - Then 메뉴는 카드 형태로, 터치 버튼은 최소 44x44px이다.

## US-MENU-02 — 고객 카테고리별 메뉴 탐색
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 카테고리별로 분류된 메뉴를 빠르게 이동하며 보기를, **so that** 원하는 메뉴를 쉽게 찾는다.
- **Acceptance Criteria**
  - Given 카테고리가 여러 개, When 카테고리를 선택하면, Then 해당 카테고리 메뉴만 표시된다.
  - Then 카테고리 간 빠른 이동이 가능하다.

## US-MENU-03 — 고객 메뉴 상세 확인
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 메뉴명·가격·설명·이미지를 보기를, **so that** 무엇을 주문할지 결정한다.
- **Acceptance Criteria**
  - Given 메뉴 항목, When 상세를 보면, Then 메뉴명/가격/설명/이미지(URL)가 표시된다.
  - Given 이미지 URL이 유효하지 않으면, Then 대체 표시(placeholder)로 처리된다. `[RES-10 그레이스풀 디그레이드]`

## US-MENU-04 — 관리자 메뉴 등록
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 메뉴명·가격·설명·카테고리·이미지 URL로 메뉴를 등록하기를, **so that** 고객에게 최신 메뉴를 제공한다.
- **Acceptance Criteria**
  - Given 필수 필드가 모두 입력, When 등록하면, Then 메뉴가 생성되어 목록/고객 화면에 반영된다.
  - Given 필수 필드 누락 또는 가격 범위 위반, When 등록하면, Then 검증 오류가 표시되고 저장되지 않는다. `[SEC-05 입력검증]`
- **확장 요구**: `[PBT-03]` 가격 범위 불변식(가격 ≥ 0, 상한 내) 속성 테스트.

## US-MENU-05 — 관리자 메뉴 수정
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 기존 메뉴 정보를 수정하기를, **so that** 가격·설명 변경을 즉시 반영한다.
- **Acceptance Criteria**
  - Given 기존 메뉴, When 필드를 수정·저장하면, Then 변경이 반영되고 검증 규칙이 동일 적용된다. `[SEC-05]`
  - Given 다른 매장의 메뉴 ID, When 수정을 시도하면, Then 거부된다. `[SEC-08 IDOR 방지]`

## US-MENU-06 — 관리자 메뉴 삭제
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 메뉴를 삭제하기를, **so that** 판매 중단 메뉴를 목록에서 제거한다.
- **Acceptance Criteria**
  - Given 메뉴, When 삭제하면, Then 목록/고객 화면에서 제거된다.
  - Given 자기 매장 메뉴만, Then 삭제 가능하다. `[SEC-08]`

## US-MENU-07 — 관리자 메뉴 노출 순서 조정
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 메뉴 노출 순서를 조정하기를, **so that** 추천 메뉴를 앞에 배치한다.
- **Acceptance Criteria**
  - Given 여러 메뉴, When 순서를 변경·저장하면, Then 고객 화면에 그 순서대로 표시된다.

---

# EPIC-ORDER — 주문 (장바구니 · 생성 · 내역 · 모니터링)

## US-ORDER-01 — 고객 장바구니 담기/삭제
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 메뉴를 장바구니에 담고 뺄 수 있기를, **so that** 주문할 항목을 구성한다.
- **Acceptance Criteria**
  - Given 메뉴, When 담기를 누르면, Then 장바구니에 추가된다. When 삭제하면, Then 제거된다.

## US-ORDER-02 — 고객 장바구니 수량 조절 및 총액 계산
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 수량을 증감하고 총액이 실시간 계산되기를, **so that** 결제 전 금액을 안다.
- **Acceptance Criteria**
  - Given 장바구니 항목, When 수량을 변경하면, Then 총액 = Σ(단가 × 수량)으로 즉시 재계산된다.
- **확장 요구**: `[PBT-03]` 총액 불변식(총액 = Σ 단가×수량), `[PBT-06]` 장바구니 상태 기반 테스트(담기/빼기/수량변경 시퀀스 후 총액·항목 일관성).

## US-ORDER-03 — 고객 장바구니 로컬 유지
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 새로고침해도 장바구니가 유지되기를, **so that** 실수로 새로고침해도 다시 담지 않는다.
- **Acceptance Criteria**
  - Given 장바구니에 항목이 있고, When 페이지를 새로고침하면, Then 항목이 그대로 유지된다(클라이언트 로컬 저장).
  - Then 서버 전송은 주문 확정 시에만 발생한다.
- **확장 요구**: `[PBT-02]` 장바구니 로컬 저장/복원 라운드트립(직렬화→역직렬화 = 원본).

## US-ORDER-04 — 고객 장바구니 비우기
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 장바구니를 한 번에 비우기를, **so that** 새로 구성한다.
- **Acceptance Criteria**
  - Given 항목이 있는 장바구니, When 비우기를 누르면, Then 모든 항목이 제거되고 총액은 0이 된다.

## US-ORDER-05 — 고객 주문 확정
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 장바구니 내용을 주문으로 확정하기를, **so that** 주방/매장에 주문이 전달된다.
- **Acceptance Criteria**
  - Given 장바구니에 항목이 있고, When 주문을 확정하면, Then 주문이 생성되고 주문번호가 표시된 뒤 장바구니가 비워지고 메뉴 화면으로 리다이렉트된다.
  - Then 주문 정보에 매장 식별·테이블 식별·메뉴 목록(메뉴명·수량·단가)·총액·세션 ID가 포함된다.
  - Given 빈 장바구니, When 확정을 시도하면, Then 거부된다. `[SEC-05]`
- **확장 요구**: `[SEC-05]` 서버측 입력검증·파라미터라이즈드 저장, `[SEC-08]` 세션·테이블 소유권 검증.

## US-ORDER-06 — 고객 주문 실패 처리
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 주문이 실패하면 명확한 안내와 함께 장바구니가 유지되기를, **so that** 다시 시도할 수 있다.
- **Acceptance Criteria**
  - Given 서버 오류로 주문 확정이 실패, When 응답을 받으면, Then 오류 메시지가 표시되고 장바구니는 그대로 유지된다. `[SEC-15 fail-closed]` `[RES-10]`

## US-ORDER-07 — 고객 현재 세션 주문 내역 조회
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 현재 테이블 세션의 주문 내역만 보기를, **so that** 이전 손님 주문과 혼동하지 않는다.
- **Acceptance Criteria**
  - Given 여러 주문이 있는 현재 세션, When 내역을 조회하면, Then 현재 세션 주문만 시간순으로 표시된다(이전 세션·이용완료 주문 제외).
  - Then 주문별 주문번호·시각·메뉴/수량·금액·상태(대기중/준비중/완료)가 표시된다.
  - Then 페이지네이션 또는 무한 스크롤을 지원한다.
- **확장 요구**: `[SEC-08]` 현재 세션·테이블 범위로만 필터(타 세션 접근 불가).

## US-ORDER-08 — 고객 주문 상태 실시간 업데이트(SSE)
- **Persona**: 고객(지민)
- **As a** 고객, **I want** 주문 상태 변화가 실시간으로 반영되기를, **so that** 새로고침 없이 진행 상황을 안다.
- **Acceptance Criteria**
  - Given 내역 화면을 보는 중, When 관리자가 상태를 변경하면, Then SSE로 상태가 실시간 갱신된다.
  - Given SSE 연결이 끊기면, When 재연결되면, Then 최신 상태로 복구된다. `[RES-10 타임아웃/재연결]`

## US-ORDER-09 — 관리자 실시간 주문 모니터링(그리드)
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 테이블별 그리드에서 주문을 실시간으로 보기를, **so that** 신규 주문을 놓치지 않는다.
- **Acceptance Criteria**
  - Given 대시보드를 보는 중, When 신규 주문이 들어오면, Then 2초 이내에 SSE로 표시된다.
  - Then 테이블별 카드에 총 주문액과 최신 주문 n개 미리보기가 표시된다.
  - Then 신규 주문은 시각적으로 강조(색상/애니메이션)된다.
- **확장 요구**: `[RES-05]` 관측성(연결/지연 메트릭), `[RES-10]` SSE 타임아웃/재연결.

## US-ORDER-10 — 관리자 주문 상세 보기
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 주문 카드를 눌러 전체 메뉴 목록을 보기를, **so that** 정확히 준비한다.
- **Acceptance Criteria**
  - Given 주문 카드, When 클릭하면, Then 전체 메뉴/수량/단가/총액 상세가 표시된다.

## US-ORDER-11 — 관리자 주문 상태 변경
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 주문 상태를 대기중→준비중→완료로 변경하기를, **so that** 진행 상황을 관리하고 고객에게 반영한다.
- **Acceptance Criteria**
  - Given 주문, When 상태를 변경하면, Then 저장되고 관리자·고객 화면(SSE)에 반영된다.
  - Given 자기 매장 주문만, Then 상태 변경이 가능하다. `[SEC-08]`

## US-ORDER-12 — 관리자 테이블별 필터링
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 특정 테이블로 필터링하기를, **so that** 바쁜 시간에 특정 테이블에 집중한다.
- **Acceptance Criteria**
  - Given 여러 테이블 주문, When 테이블을 선택하면, Then 해당 테이블 주문만 표시된다.

---

# EPIC-SESSION — 테이블 · 세션 · 이력

## US-SESSION-01 — 세션 시작(첫 주문)
- **Persona**: 관리자(현우) / 시스템
- **As a** 매장 운영자, **I want** 테이블의 첫 주문 시 세션이 시작되기를, **so that** 한 손님 그룹의 주문을 묶어 관리한다.
- **Acceptance Criteria**
  - Given 활성 세션이 없는 테이블, When 첫 주문이 생성되면, Then 새 테이블 세션이 시작되고 이후 주문이 이 세션에 귀속된다.
- **확장 요구**: `[PBT-06]` 세션 상태 기반 테스트.

## US-SESSION-02 — 관리자 주문 직권 삭제
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 특정 주문을 삭제하기를, **so that** 오주문/중복을 정정한다.
- **Acceptance Criteria**
  - Given 주문, When 삭제 버튼을 누르면, Then 확인 팝업이 표시된다.
  - Given 확인, When 삭제하면, Then 주문이 즉시 삭제되고 테이블 총 주문액이 재계산되며 성공 피드백이 표시된다.
  - Given 삭제 대상은 자기 매장 주문만. `[SEC-08]`
- **확장 요구**: `[PBT-03]` 삭제 후 총액 = Σ(잔여 주문) 불변식, `[SEC-13]` 데이터 변경 감사 로깅(누가·언제·무엇).

## US-SESSION-03 — 관리자 테이블 이용 완료(세션 종료)
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 테이블 이용 완료를 처리하기를, **so that** 다음 손님이 이전 주문 없이 시작한다.
- **Acceptance Criteria**
  - Given 활성 세션, When 이용 완료를 누르면, Then 확인 팝업이 표시된다.
  - Given 확인, When 처리하면, Then 해당 세션 주문이 과거 이력(OrderHistory)으로 이동하고 완료 시각이 기록된다.
  - Then 테이블의 현재 주문 목록·총 주문액이 0으로 리셋된다.
  - Then 새 고객이 이전 주문 내역 없이 시작 가능하다.
- **확장 요구**: `[PBT-04]` 멱등성(이미 종료된 세션에 종료 재적용 시 상태 불변), `[PBT-03]` 종료 후 현재 총액=0 불변식, `[PBT-06]` 세션 라이프사이클 상태 기반 테스트.

## US-SESSION-04 — 관리자 과거 주문 내역 조회
- **Persona**: 관리자(현우)
- **As a** 매장 관리자, **I want** 테이블별 과거 주문 내역을 조회하기를, **so that** 정산·확인에 활용한다.
- **Acceptance Criteria**
  - Given "과거 내역" 버튼, When 누르면, Then 테이블별 과거 주문이 시간 역순으로 표시된다.
  - Then 각 주문에 주문번호·시각·메뉴 목록·총액·이용 완료 시각이 표시된다.
  - Then 날짜 필터링이 가능하고 "닫기"로 대시보드로 복귀한다.
  - Given 자기 매장 이력만 조회 가능. `[SEC-08]`

---

# EPIC-TENANT — 멀티테넌시 및 횡단 관심사

## US-TENANT-01 — 매장 단위 데이터 격리
- **Persona**: 공통(고객/관리자)
- **As a** 시스템 이해관계자, **I want** 모든 데이터가 매장 식별자로 격리되기를, **so that** 한 매장이 다른 매장 데이터에 접근하지 못한다.
- **Acceptance Criteria**
  - Given 매장 A의 인증 주체, When 매장 B의 리소스(메뉴/주문/세션/이력) ID로 접근을 시도하면, Then 거부된다. `[SEC-08 IDOR 방지]`
  - Then 모든 조회/변경 쿼리는 매장 식별자로 스코프된다.
- **확장 요구**: `[PBT-03]` 테넌트 격리 불변식(임의 매장/리소스 조합에서 교차 접근 불가).

## US-TENANT-02 — 입력 검증 및 인젝션 방지(횡단)
- **Persona**: 공통 / 개발팀(기술 스토리)
- **As a** 시스템, **I want** 모든 API 입력이 검증되고 파라미터라이즈드 쿼리를 쓰기를, **so that** 인젝션·XSS를 방지한다.
- **Acceptance Criteria**
  - Given 임의 API 입력, When 처리 전에, Then 타입/길이/형식이 검증되고 위반 시 거부된다. `[SEC-05]`
  - Then 모든 DB 접근은 파라미터라이즈드 쿼리를 사용한다(문자열 결합 금지). `[SEC-05]`
- **확장 요구**: `[PBT-07]` 도메인 생성기 기반 입력 퍼징으로 검증 견고성 확인.

## US-TENANT-03 — 보안 헤더 및 CORS(횡단)
- **Persona**: 공통 / 개발팀(기술 스토리)
- **As a** 시스템, **I want** HTML 제공 엔드포인트에 보안 헤더를, 인증 엔드포인트에 CORS 화이트리스트를 적용하기를, **so that** 브라우저 공격면을 줄인다.
- **Acceptance Criteria**
  - Then CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy가 설정된다. `[SEC-04]`
  - Then 인증 엔드포인트 CORS는 명시적 허용 오리진만 허용(와일드카드 금지). `[SEC-08]`

## US-TENANT-04 — 구조적 로깅 및 보안 이벤트 알림(횡단)
- **Persona**: 관리자/운영 / 개발팀(기술 스토리)
- **As a** 운영자, **I want** 구조적 로깅과 보안 이벤트 알림을, **so that** 문제를 추적하고 대응한다.
- **Acceptance Criteria**
  - Then 로그에 타임스탬프·상관ID·레벨·메시지가 포함되고 민감정보(비밀번호/토큰/PII)는 로깅되지 않는다. `[SEC-03]`
  - Then 인증 실패·인가 거부 등 보안 이벤트가 알림 대상이 된다. `[SEC-14]`
  - Then 기존 조직 인시던트 대응 프로세스로 알림이 연계된다(참조 추후 확정). `[RES-15]`

## US-TENANT-05 — 헬스 체크 및 백업(횡단)
- **Persona**: 운영 / 개발팀(기술 스토리)
- **As a** 운영자, **I want** 헬스 체크와 자동 백업을, **so that** 장애를 감지하고 데이터를 복구한다.
- **Acceptance Criteria**
  - Then 각 서비스가 헬스 체크 엔드포인트를 제공하고, 크리티컬 서비스는 DB 연결을 확인하는 딥 헬스체크를 제공한다. `[RES-06]`
  - Then 영속 데이터에 자동 백업이 구성되고(암호화·보존 정책), 복원 검증 절차가 문서화된다(DR 전략: Backup & Restore). `[RES-12]` `[RES-02]`

---

## 부록 A: Epic ↔ 요구사항 추적
| Epic | 관련 요구사항 |
|------|----------------|
| EPIC-AUTH | FR-A1, FR-C1, FR-A3(초기 설정) |
| EPIC-MENU | FR-C2, FR-A4 |
| EPIC-ORDER | FR-C3, FR-C4, FR-C5, FR-A2 |
| EPIC-SESSION | FR-A3(주문 삭제/세션/이력) |
| EPIC-TENANT | FR-MT1, FR-MT2, NFR-S/R 횡단 |

## 부록 B: 통계
- 총 스토리: 33개 (AUTH 5, MENU 7, ORDER 12, SESSION 4, TENANT 5)
- 페르소나: 2 (고객, 관리자) + 횡단(기술) 스토리
- 확장 커버리지: SEC(01·03·04·05·08·12·13·14·15), RES(02·05·06·10·12·15), PBT(02·03·04·06·07)
