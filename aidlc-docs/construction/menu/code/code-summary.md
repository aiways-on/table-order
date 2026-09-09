# Code Summary — U3 menu

**Phase**: CONSTRUCTION → Code Generation (Part 2 완료)
**Unit**: U3 menu
**Stories**: US-MENU-01~07 (모두 구현·검증)
**검증**: 로컬 throwaway venv에서 `pytest` 실행 → **57 passed** (U1 14 + U2 24 + U3 19). venv는 커밋하지 않고 삭제함.

---

## 생성/수정 파일

### 앱 코드 (`backend/app/menu/`)
| 파일 | 내용 | 관련 규칙 |
|------|------|-----------|
| `__init__.py` | 패키지 스캐폴딩 | — |
| `schemas.py` | MenuCreate/MenuUpdate(name 1~100·price≥0·category 1~50·description≤500·image_url http(s)≤500, blank 금지), MenuOut, MenuCategoryGroup, MenuGroupedResponse, ReorderRequest/Response | SEC-05, BR-M01~M06 |
| `repository.py` | `MenuRepository(TenantScopedRepository[Menu])` — model=Menu, `list_ordered()`(display_order,name), `max_display_order()`(append 기준) | SEC-08 |
| `service.py` | `MenuService`: list_flat/list_grouped(BR-M19 결정적 그룹핑), get, create(BR-M13 자동 display_order), update(전체 필드 교체), delete(soft), reorder(BR-M14/M16 원자적 순열 검증) | BR-M07~M20, SEC-08/15 |
| `router.py` | `/api/menus` 엔드포인트, `require_viewer`(관리자 쿠키 or 고객 세션 토큰) 조회 가드, `require_admin` 쓰기 가드, db.commit() 경계 | BR-M08, SEC-08 |

### 수정된 파일
| 파일 | 변경 |
|------|------|
| `app/main.py` | menu 라우터 등록 |

### 테스트 (`backend/tests/`, 19 신규)
| 파일 | 커버리지 |
|------|----------|
| `test_menu_service.py` | 자동 display_order, 수정, 소프트삭제 제외·재삭제 404, 그룹 정렬, 재정렬 순열·불완전집합·외부id 거부, 교차 테넌트 404 |
| `test_menu_properties.py` | Hypothesis PBT: BR-M15 테넌트 격리, BR-M16 재정렬 순열 보존, BR-M17 소프트삭제 단조성, BR-M18 가격 왕복 (예제마다 신규 in-memory DB) |
| `test_menu_api.py` | 미인증 401, 관리자 등록·목록, 음수 가격 422, 고객 조회 가능·쓰기 401, 재정렬 흐름, 삭제, 교차 테넌트 404 |

---

## 검증 중 발견·수정한 사항 (설계상 중요)
- **컨텍스트 스레드 전파 버그**: 동기(sync) 경로 오퍼레이션과 그 동기 의존성은 각기 다른 threadpool 워커에서 실행되며 **contextvars 사본을 독립적으로 가진다**. 따라서 가드(`require_admin`/`require_viewer`)에서 `set_context()`로 심은 `TenantContext`가 엔드포인트 본문 스레드(여기서 `MenuRepository`가 contextvar를 읽음)에서는 보이지 않아 `require_store_id()`가 403을 던졌다.
  - **해결**: 각 엔드포인트가 가드가 반환한 `ctx`를 본문 첫 줄에서 `set_context(ctx)`로 **자기 스레드에 재확립**. (U2는 store_id를 서비스에 명시적으로 전달했기에 이 문제에 노출되지 않았음 — 회귀 아님.) 근거를 router.py 상단 주석에 명시.

---

## 제공 계약 (하위 단위/프론트)
- `GET /api/menus` (카테고리 그룹), `GET /api/menus/flat` (평면, display_order 순), `GET /api/menus/{id}` — require_viewer(고객·관리자)
- `POST /api/menus`(201), `PUT /api/menus/{id}`, `DELETE /api/menus/{id}`(204), `POST /api/menus/reorder` — require_admin
- `MenuService` — U4 order가 주문 생성 시 단가·명 스냅샷 조회에 재사용 가능

## 확장 규칙 준수 요약
| 확장 | 상태 | 근거 |
|------|:---:|------|
| Security Baseline | ✅ | 입력 검증(SEC-05), 조회/쓰기 권한 경계·테넌트 격리 이중 방어·IDOR 404(SEC-08), fail-closed 중앙 오류(SEC-15) |
| Property-Based Testing | ✅ | Hypothesis 불변식 4종(BR-M15~M18) |
| Resiliency Baseline | ✅(해당) | 재정렬 원자성(부분 반영 없음), 중앙 오류 처리; 인프라·백업은 U1 확정(N/A) |

---

## 마이그레이션 / 배포
- **신규 DB 테이블 없음** — U1 `Menu` 모델 재사용 → Alembic 마이그레이션 불필요.
- 배포 아티팩트 변경 없음.
