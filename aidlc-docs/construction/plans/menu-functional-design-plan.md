# Functional Design 계획 — U3 menu (Part 1: Planning / Questions)

**단계**: CONSTRUCTION → Functional Design
**단위**: U3 menu
**구현 스토리**: US-MENU-01~07 (고객 메뉴 조회/카테고리/상세, 관리자 등록/수정/삭제/노출순서)
**승계 컨텍스트**: U1 `app/shared/models.Menu`(store_id, name, price int≥0, category, image_url, display_order, deleted_at 소프트삭제, 복합 인덱스), `TenantScopedRepository`(테넌트 격리·소프트삭제 자동), `app/core`(errors, context, logging); U2 인증 가드 `require_admin`/`require_customer`.

> **Menu ORM 엔티티는 U1에서 이미 정의됨** → 신규 테이블/마이그레이션 없음. 본 설계는 서비스/스키마/라우터 계층의 비즈니스 규칙을 확정합니다.

---

## 확인 질문 (A/B/C 중 택1, 필요 시 X로 자유 기술)

각 질문의 `[Answer]:` 뒤에 선택지를 적어주세요. "모두 A" 같은 일괄 응답도 가능합니다.

### Q1. 카테고리 모델링
- **A.** 메뉴의 `category` 문자열 필드를 그대로 사용하고, 고객 화면 카테고리 목록은 매장 내 distinct category를 동적으로 도출 (별도 카테고리 엔티티 없음) — U1 모델과 일치, 단순
- **B.** 별도 Category 테이블 신설(정렬·이름 관리) — 신규 테이블/마이그레이션 필요
- **C.** 카테고리 없이 단일 목록만

[Answer]: A

### Q2. 품절/노출 토글
- **A.** 별도 품절 플래그 없음 — 판매 중단은 소프트 삭제(US-MENU-06)로 처리 (스토리에 품절 요구 없음, 최소 구현)
- **B.** `is_available` 플래그 추가(품절 표시, 목록엔 남기되 주문 불가) — 모델 필드 추가 필요
- **C.** 하드 삭제만 사용

[Answer]: A

### Q3. 노출 순서 조정 방식 (US-MENU-07)
- **A.** 일괄 재정렬 엔드포인트 — 정렬된 menu_id 배열을 받아 `display_order`를 0..n으로 재할당 (원자적, 프론트 드래그앤드롭에 적합)
- **B.** 개별 메뉴의 display_order 직접 지정(수정 API에 포함)
- **C.** 순서 조정 미지원(등록순 고정)

[Answer]: A

### Q4. 삭제 의미론
- **A.** 소프트 삭제 — `deleted_at` 설정(U1 모델 기존 필드), 모든 조회(고객·관리자)에서 제외, 과거 주문 이력의 메뉴명·단가는 주문 스냅샷으로 보존(U4 담당)
- **B.** 하드 삭제(행 제거)
- **C.** 소프트 삭제하되 관리자 화면에는 "삭제됨"으로 표시

[Answer]: A

### Q5. 고객 메뉴 목록 응답 구성 (US-MENU-01/02/03)
- **A.** 카테고리별 그룹 + 각 그룹 내 `display_order` 정렬, 항목마다 전체 필드(명·가격·설명·이미지) 포함 → 상세(US-MENU-03)도 목록 데이터로 충족, 별도 상세 호출 불필요(추가로 단건 GET도 제공)
- **B.** 평면 목록만 반환(프론트가 클라이언트에서 그룹핑)
- **C.** 목록은 요약 필드만, 상세는 반드시 단건 GET

[Answer]: A

### Q6. 검증 규칙 (SEC-05)
- **A.** name 필수(1~100자), price 정수 KRW ≥0(모델 CheckConstraint 일치), category 필수(1~50자), description 선택(≤500자), image_url 선택(≤500자, http/https 형식 검증) — 등록·수정 동일 적용
- **B.** 최소 검증(name·price만 필수)
- **C.** 더 엄격(이미지 URL 도달성 검사 등)

[Answer]: A

### Q7. 권한 경계
- **A.** 조회(GET 목록/단건)는 `require_customer`(활성 세션) 및 `require_admin` 모두 허용; 쓰기(생성/수정/삭제/재정렬)는 `require_admin` 전용. 모든 접근은 store_id로 테넌트 격리 + 서비스 계층 소유권 재확인(IDOR 방지 SEC-08)
- **B.** 고객 조회는 인증 없이 store_code로 공개
- **C.** 조회도 관리자 전용

[Answer]: A

---

## 산출 예정 문서 (승인 후 생성)
- `aidlc-docs/construction/menu/functional-design/menu-logic-model.md` — 메뉴 조회/등록/수정/삭제/재정렬 로직, 카테고리 도출, 고객 vs 관리자 뷰, U1/U2 계약 배선
- `aidlc-docs/construction/menu/functional-design/menu-business-rules.md` — BR-M01~ (검증·테넌트 격리·소프트삭제·재정렬 불변식; PBT 대상 불변식 포함)

---

**질문에 답해주시면 답변을 audit.md에 기록하고, 모호함이 없으면 Part 2(설계 문서 생성)로 진행합니다.**
