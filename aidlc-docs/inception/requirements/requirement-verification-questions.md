# 요구사항 확인 질문 (Requirements Verification Questions)

아래 질문에 각 `[Answer]:` 태그 뒤에 **선택지 문자(A, B, C ...)**를 채워 답변해 주세요.
제시된 선택지가 맞지 않으면 마지막 옵션(Other)을 선택하고 `[Answer]:` 뒤에 직접 설명해 주세요.
모두 작성하신 후 "완료" 또는 "done"이라고 알려주시면 다음 단계로 진행합니다.

제공해주신 `table-order-requirements.md`와 `constraints.md`는 기능 요구사항이 매우 상세합니다. 아래는 구현 방향을 확정하기 위해 명시되지 않은 **기술·범위·운영** 관련 사항을 확인하는 질문입니다.

---

## Question 1
이 서비스는 여러 매장을 지원하는 멀티테넌트 구조인가요, 아니면 단일 매장용인가요? (요구사항에 "매장 식별자"가 등장합니다.)

A) 멀티테넌트 - 하나의 시스템에서 여러 매장을 매장 식별자로 구분하여 운영

B) 단일 매장 - 하나의 매장만 운영 (매장 식별자는 단순 상수/설정값)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
백엔드(서버 시스템) 기술 스택 선호가 있나요?

A) Python (FastAPI 등)

B) Node.js / TypeScript (Express, NestJS 등)

C) Java / Kotlin (Spring Boot 등)

D) 특별한 선호 없음 - AI가 요구사항(SSE 실시간, JWT, bcrypt 등)에 적합하게 추천

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
프론트엔드(고객용/관리자용 웹 UI) 기술 스택 선호가 있나요? (요구사항상 브라우저에서 동작하는 웹 UI)

A) React (예: Vite + React)

B) Vue

C) 순수 HTML/CSS/JavaScript (프레임워크 없음)

D) 특별한 선호 없음 - AI가 추천

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
데이터 저장소(매장/메뉴/주문/주문이력)로 어떤 종류를 사용할까요?

A) 관계형 데이터베이스 (PostgreSQL, MySQL 등)

B) NoSQL (DynamoDB, MongoDB 등)

C) 개발/데모 편의를 위한 경량 DB (SQLite 등)

D) 특별한 선호 없음 - AI가 추천

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
배포/실행 환경 목표는 무엇인가요? (AI-DLC 규칙은 AWS 기반 가이드를 포함합니다.)

A) 로컬 개발 환경 위주 (docker-compose 등으로 로컬 실행, 데모/학습 목적)

B) AWS 클라우드 배포 (예: 컨테이너/서버리스 + 관리형 DB)

C) 컨테이너 기반이되 클라우드 중립적 (Docker, 특정 클라우드 비종속)

D) 특별한 선호 없음 - AI가 추천

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6
예상 사용 규모(동시성)는 어느 정도인가요? 성능/확장성 설계 수준을 판단하는 데 사용됩니다.

A) 소규모 - 매장당 수~수십 테이블, 데모/MVP 수준

B) 중규모 - 다수 매장, 매장당 수십~수백 테이블

C) 대규모 - 많은 매장과 높은 동시 주문량, 확장성 중요

D) 특별한 선호 없음 - MVP에 맞춰 합리적 기본값 사용

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
메뉴 이미지는 요구사항상 "이미지 URL" 입력 방식입니다(파일 업로드/리사이징은 constraints에서 제외). 이 방향이 맞나요?

A) 예 - 외부 이미지 URL을 저장/표시하는 방식으로 구현 (업로드 없음)

B) 아니오 - 이미지 업로드 기능이 필요함 (constraints와 상충하므로 재확인 필요)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8
주문 내역 조회의 "주문 상태 실시간 업데이트"는 요구사항에서 (선택사항)으로 표기되어 있습니다. MVP에 포함할까요?

A) 포함 - 고객 화면에서도 SSE 등으로 주문 상태 실시간 반영

B) 제외 - MVP에서는 고객 화면은 새로고침/재조회 기반, 관리자 화면만 실시간(SSE)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 확장(Extensions) 적용 여부

AI-DLC에는 선택 가능한 확장 규칙이 있습니다. 아래 3가지 확장의 적용 여부를 선택해 주세요.

## Question 9: 보안 확장 (Security Baseline)
이 프로젝트에 보안 확장 규칙을 강제 적용할까요?

A) 예 - 모든 보안(SECURITY) 규칙을 차단성(blocking) 제약으로 강제 (프로덕션 수준 애플리케이션 권장)

B) 아니오 - 보안 규칙 전체 생략 (PoC, 프로토타입, 실험적 프로젝트에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 10: 속성 기반 테스트 확장 (Property-Based Testing)
이 프로젝트에 속성 기반 테스트(PBT) 규칙을 강제 적용할까요?

A) 예 - 모든 PBT 규칙을 차단성 제약으로 강제 (비즈니스 로직, 데이터 변환, 직렬화, 상태 저장 컴포넌트가 있는 프로젝트 권장)

B) 부분 - 순수 함수 및 직렬화 왕복(round-trip)에 대해서만 PBT 규칙 적용 (알고리즘 복잡도가 제한적인 프로젝트에 적합)

C) 아니오 - 모든 PBT 규칙 생략 (단순 CRUD, UI 전용, 얇은 통합 계층 프로젝트에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11: 복원력 확장 (Resiliency Baseline)
이 프로젝트에 복원력(Resiliency) 베이스라인을 적용할까요?

이 확장은 AWS Well-Architected Framework(신뢰성 기둥) 기반의 **설계 단계 모범 사례(방향성 가이드)**를 적용합니다. 내결함성, 고가용성, 관찰가능성, 복구가능성 방향으로 요구사항/설계/코드를 유도합니다. 단, 이것이 프로덕션 준비 완료나 특정 가용성/RTO/RPO 보장을 의미하지는 않으며, 검증·강화가 필요한 **초안** 수준입니다.

A) 예 - 복원력 베이스라인을 설계 단계 방향성 가이드로 적용 (비즈니스 크리티컬 워크로드 권장, 이후 검증·강화 전제)

B) 아니오 - 복원력 베이스라인 생략 (빠른 반복이 더 중요한 PoC, 프로토타입, 실험적 프로젝트에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: A
