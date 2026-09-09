# Code Generation 계획 — U3 menu (Part 1: Planning)

**단계**: CONSTRUCTION → Code Generation
**단위**: U3 menu
**코드 위치**: `backend/app/menu/` (앱 코드), 문서 `aidlc-docs/construction/menu/code/`
**이 계획이 Code Generation의 단일 진실 원천입니다.**

---

## 단위 컨텍스트
**구현 스토리**: US-MENU-01(고객 기본화면), US-MENU-02(카테고리 탐색), US-MENU-03(상세), US-MENU-04(등록), US-MENU-05(수정), US-MENU-06(삭제), US-MENU-07(노출순서).

**의존성(승계)**: U1 `app/shared`(models.Menu, TenantScopedRepository, schemas.PagedResponse), `app/core`(context, errors, database, logging); U2 `app/auth/dependencies`(require_admin/require_customer). **하위 소비자**: U4 order(메뉴 단가·명 스냅샷), U5/U6 프론트.

**소유 로직**: 메뉴 서비스/리포지토리/스키마/라우터. **신규 DB 테이블 없음** → 마이그레이션 불필요.

**제공 계약**:
- `GET /api/menus` (그룹, `?flat=true` 평면), `GET /api/menus/{id}` — 조회(require_customer|require_admin)
- `POST /api/menus`, `PUT /api/menus/{id}`, `DELETE /api/menus/{id}`, `POST /api/menus/reorder` — 쓰기(require_admin)
- `MenuService`(U4가 주문 검증 시 단가·명 조회에 재사용)

---

## 실행 단계 (Numbered Steps)

### Step 1: 모듈 구조
- [x] `app/menu/__init__.py`
- 경로: `backend/app/menu/`

### Step 2: 스키마 (API 계약 · 검증 SEC-05) — BR-M01~M06
- [x] `app/menu/schemas.py` (MenuCreate, MenuUpdate, MenuOut, MenuCategoryGroup, MenuGroupedResponse, ReorderRequest — name 1~100, price int≥0, category 1~50, description ≤500, image_url http(s) ≤500)
- 경로: `backend/app/menu/`

### Step 3: 리포지토리
- [x] `app/menu/repository.py` (`MenuRepository(TenantScopedRepository[Menu])` — model=Menu; list/get/add/soft_delete 상속, 필요 시 정렬 헬퍼)
- 경로: `backend/app/menu/`

### Step 4: 서비스 (Business Logic) — BR-M07~M20
- [x] `app/menu/service.py` (`MenuService`: list_grouped, list_flat, get, create[display_order 자동], update, delete[soft], reorder[원자적 순열 검증]; 테넌트 격리·IDOR 이중 방어)
- 경로: `backend/app/menu/`

### Step 5: API 라우터
- [x] `app/menu/router.py` (`/api/menus` — 조회 require_customer|require_admin 허용, 쓰기 require_admin; db.commit() 경계)
- [x] `app/main.py`에 menu 라우터 등록 (기존 파일 수정)
- 경로: `backend/app/menu/`, `backend/app/main.py`

### Step 6: 단위 + 속성 테스트 (PBT)
- [x] `tests/test_menu_service.py` (등록/자동 display_order, 수정, 소프트삭제 제외, 재정렬 원자성·오류, 타 매장 404)
- [x] `tests/test_menu_properties.py` (Hypothesis: BR-M15 테넌트 격리, BR-M16 재정렬 순열 보존, BR-M17 소프트삭제 단조성, BR-M18 가격 왕복) [PBT-03/07]
- [x] `tests/test_menu_api.py` (조회 가드[고객·관리자], 쓰기 관리자 전용 401/403, 그룹 응답, reorder 흐름)
- 경로: `backend/tests/`

### Step 7: 문서
- [x] `aidlc-docs/construction/menu/code/code-summary.md`
- 경로: `aidlc-docs/construction/menu/code/`

---

## 스토리 추적성
| 스토리 | 구현 위치 | 상태 |
|--------|-----------|:---:|
| US-MENU-01 고객 기본화면 | service.list_grouped, router GET | [x] |
| US-MENU-02 카테고리 탐색 | service.list_grouped(그룹핑/정렬) | [x] |
| US-MENU-03 상세 | schemas.MenuOut, router GET/{id} | [x] |
| US-MENU-04 등록 | service.create, schemas.MenuCreate | [x] |
| US-MENU-05 수정 | service.update, schemas.MenuUpdate | [x] |
| US-MENU-06 삭제 | service.delete(soft) | [x] |
| US-MENU-07 노출순서 | service.reorder, schemas.ReorderRequest | [x] |

---

## 범위 요약
- **총 7단계**. 신규 DB 테이블 없음(U1 Menu 재사용) → 마이그레이션 불필요.
- 배포 아티팩트 변경 없음(기존 compose/backend 이미지에 포함).
- 테스트는 생성만, 실행은 Build & Test. 생성 후 로컬 pytest로 검증 예정.

---

**이 계획을 승인하시면 Part 2(코드 생성)로 진행합니다.**
