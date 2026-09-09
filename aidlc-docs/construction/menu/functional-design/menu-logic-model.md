# Menu — Functional Logic Model (U3)

**단위**: U3 menu | **스토리**: US-MENU-01~07
**결정(모두 A)**: 카테고리=문자열 필드, 품절=소프트삭제로 대체, 재정렬=일괄 API, 삭제=소프트, 고객 목록=카테고리 그룹+전체필드, 검증=SEC-05 표준, 권한=조회(고객·관리자)/쓰기(관리자).

> Menu ORM 엔티티는 U1 `app/shared/models.Menu`에 이미 존재 → **신규 테이블/마이그레이션 없음**.

---

## 1. 승계 계약 배선 (U1/U2 → U3)

| 필요 | 출처 | 사용처 |
|------|------|--------|
| `Menu` 모델 (store_id, name, price, category, image_url, display_order, deleted_at) | U1 `app/shared/models` | 리포지토리 |
| `TenantScopedRepository` (store_id 강제 필터 + deleted_at IS NULL) | U1 `app/shared/repository` | `MenuRepository` |
| `require_admin` / `require_customer` (컨텍스트 확립) | U2 `app/auth/dependencies` | 라우터 가드 |
| `require_store_id()` / `get_context()` | U1 `app/core/context` | 서비스 테넌트 스코프 |
| `NotFoundError` / `ForbiddenError` / `ValidationError` | U1 `app/core/errors` | 서비스 |

---

## 2. 컴포넌트 구조 (신규, `app/menu/`)

```
app/menu/
  __init__.py
  schemas.py       # MenuCreate, MenuUpdate, MenuOut, MenuCategoryGroup, ReorderRequest
  repository.py    # MenuRepository(TenantScopedRepository[Menu])
  service.py       # MenuService: list/list_grouped/get/create/update/delete/reorder
  router.py        # /api/menus (customer+admin read, admin write)
```

---

## 3. 로직 흐름

### 3.1 고객 메뉴 조회 — US-MENU-01/02/03
```
GET /api/menus            (require_customer | require_admin)
  → MenuService.list_grouped(store_id)
      1. repo.list()  → 자기 매장 & 미삭제 메뉴만 (테넌트 격리 자동)
      2. category 기준 그룹핑, 각 그룹 내 display_order ASC, 동순위는 name ASC
      3. 그룹 순서: 각 카테고리 최소 display_order ASC → 카테고리명 ASC
      4. MenuCategoryGroup[] 반환 (항목마다 전체 필드: 명/가격/설명/이미지)
GET /api/menus/{menu_id}  → 단건(상세). 없거나 타 매장 → 404 (존재 미노출)
```
- **평면 목록** 옵션 `GET /api/menus?flat=true` — 관리자 화면·재정렬 UI용(display_order 순).

### 3.2 관리자 등록 — US-MENU-04
```
POST /api/menus  (require_admin)
  → validate(MenuCreate)  [SEC-05]
  → repo.add(Menu(...))   # store_id는 리포지토리가 컨텍스트에서 스탬프
  → display_order 미지정 시 (max(display_order in store)+1) 자동 부여
  → 201 MenuOut
```

### 3.3 관리자 수정 — US-MENU-05
```
PUT /api/menus/{menu_id}  (require_admin)
  → repo.get_or_404(menu_id)   # 타 매장 ID → 404 (IDOR 차단, SEC-08)
  → 부분/전체 필드 갱신, 등록과 동일 검증 규칙 적용
  → 200 MenuOut
```

### 3.4 관리자 삭제 — US-MENU-06
```
DELETE /api/menus/{menu_id}  (require_admin)
  → repo.get_or_404(menu_id)
  → repo.soft_delete(menu)     # deleted_at = now; 이후 모든 조회에서 제외
  → 204
```
- 과거 주문의 메뉴명·단가는 U4 주문 스냅샷(items JSON)에 보존 → 삭제가 이력을 훼손하지 않음.

### 3.5 관리자 노출 순서 재정렬 — US-MENU-07
```
POST /api/menus/reorder  (require_admin)
  body: { "menu_ids": ["id1","id2",...] }   # 원하는 표시 순서
  → 모든 id가 자기 매장·미삭제 메뉴인지 검증 (개수·소속 일치)
      · 누락/외부/중복 id → 422 (부분 반영 없음, 원자적)
  → i번째 id의 display_order = i (0..n)
  → 단일 트랜잭션 커밋
  → 200 { updated: n }
```

---

## 4. 고객 vs 관리자 뷰 차이

| 항목 | 고객(require_customer) | 관리자(require_admin) |
|------|------------------------|------------------------|
| 조회 | 카테고리 그룹 뷰 기본 | 그룹/평면 모두 |
| 필드 | 명·가격·설명·이미지 | + id·display_order·created_at |
| 쓰기 | 불가 (403) | 등록/수정/삭제/재정렬 |
| 범위 | 활성 세션의 store_id | JWT의 store_id |

---

## 5. 검증 규칙 (SEC-05, Pydantic)
- `name`: 1~100자 필수
- `price`: int ≥ 0 (KRW; 모델 CheckConstraint와 일치)
- `category`: 1~50자 필수
- `description`: ≤500자 선택
- `image_url`: ≤500자 선택, `http(s)://` 형식 검증(도달성 검사는 하지 않음)
- 등록·수정 동일 적용

---

## 6. 관련 다이어그램 (텍스트)

```
[Customer/Admin] --HTTP--> [menu/router]
      |                         |
      | (require_customer/admin)| set TenantContext(store_id)
      v                         v
                          [MenuService] --> [MenuRepository (TenantScoped)] --> [Menu table]
                                                   |  store_id 강제 필터
                                                   |  deleted_at IS NULL
```

---

## 7. 하위 소비자
- **U5 frontend-customer**: `GET /api/menus`(그룹) — 메뉴/카테고리/상세 화면.
- **U6 frontend-admin**: 등록/수정/삭제/재정렬 + 평면 목록.
- **U4 order**: 주문 생성 시 메뉴 단가·명 조회(단건 GET 또는 서비스 직접 호출) → items 스냅샷.
