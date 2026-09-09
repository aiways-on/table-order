# Unit of Work — 테이블오더 서비스

**단계**: INCEPTION → Units Generation (Part 2)
**분해 방침**: 도메인 모듈 6단위 · 단일 배포 모듈러 모놀리스 백엔드 + 2 프론트엔드 · 모노레포 · 의존성 순차
**단위 유형**: Module (단일 배포 내 논리 모듈). "Unit of Work" = 개발 계획 단위.

---

## 코드 조직 전략 (Greenfield · 모노레포)

```text
table-order/                        # 워크스페이스 루트
├── docker-compose.yml              # backend + db (+ 정적 프론트 서빙)
├── backend/                        # U1~U4 (단일 FastAPI 서비스)
│   ├── app/
│   │   ├── main.py                 # 앱 부트스트랩, 라우터 등록, 미들웨어
│   │   ├── core/                   # U1 backend-core (횡단)
│   │   │   ├── config.py           # 설정/환경변수
│   │   │   ├── db.py               # SQLAlchemy 엔진/세션
│   │   │   ├── tenant.py           # TenantContext, store_id 스코프
│   │   │   ├── security.py         # 헤더/CORS, 오류 표준화
│   │   │   ├── logging.py          # 구조적 로깅(마스킹)
│   │   │   └── health.py           # /health, /health/deep, 백업 훅
│   │   ├── shared/                 # 공용 (Q6=A): DB 모델·Pydantic 스키마·리포지토리 베이스
│   │   │   ├── models.py           # Store, Menu, Table, TableSession, Order, OrderHistory
│   │   │   ├── schemas.py          # 공통 Pydantic 스키마
│   │   │   └── repository.py       # TenantScopedRepository 베이스
│   │   ├── auth/                   # U2 auth-session
│   │   ├── menu/                   # U3 menu
│   │   └── order/                  # U4 order (+session +realtime)
│   ├── tests/                      # 단위/통합/PBT(Hypothesis)
│   ├── migrations/                 # Alembic
│   ├── requirements.txt / pyproject.toml
│   └── Dockerfile
├── frontend-customer/              # U5 (React/Vite)
│   ├── src/  ├── Dockerfile  └── package.json
├── frontend-admin/                 # U6 (React/Vite)
│   ├── src/  ├── Dockerfile  └── package.json
└── aidlc-docs/                     # 문서 (코드 아님)
```

각 백엔드 도메인 모듈은 `router.py`(API), `service.py`(오케스트레이션), `repository.py`(데이터 접근), `schemas.py`(요청/응답)를 갖는 일관 구조를 따른다.

---

## 단위 정의

### U1. backend-core (횡단 기반)
- **책임**: 앱 부트스트랩, DB 연결/세션, TenantContext(store_id 스코프), 인가, 구조적 로깅, 보안 헤더/CORS, 입력검증 유틸, 오류 표준화(fail-closed), 헬스체크, 백업 훅, 공용 DB 모델/스키마/리포지토리 베이스.
- **컴포넌트**: TenantComponent, PlatformComponent + shared 모델.
- **확장**: SEC-03/04/05/08/15, RES-06/12/02/05.
- **비고**: 다른 모든 백엔드 단위의 기반. 최우선 개발.

### U2. auth-session (인증·세션)
- **책임**: 관리자 로그인(JWT/bcrypt)·16h 세션·시도제한, 테이블 프로비저닝·고객 자동 로그인 세션, 토큰 검증.
- **컴포넌트**: AuthComponent (Store, Table, TableSession 엔티티).
- **확장**: SEC-08/12/14.
- **의존**: U1.

### U3. menu (메뉴)
- **책임**: 메뉴 CRUD·카테고리·노출 순서·조회.
- **컴포넌트**: MenuComponent (Menu 엔티티).
- **확장**: SEC-05/08, PBT-03(가격).
- **의존**: U1, (인가) U2.

### U4. order (주문·세션·실시간)
- **책임**: 주문 확정·조회·상태·삭제, 총액 계산, 세션 라이프사이클·이용완료 이관·이력, SSE 실시간(고객/관리자).
- **컴포넌트**: OrderComponent, SessionComponent, RealtimeComponent (Order, OrderHistory 엔티티, TableSession 협력).
- **확장**: SEC-05/08/13, PBT-03/04/06/07, RES-10/05.
- **의존**: U1, U2(세션), U3(메뉴 단가 참조).

### U5. frontend-customer (고객 UI)
- **책임**: 자동 로그인 → 메뉴(카테고리/상세) → 장바구니(로컬 저장, 새로고침 유지) → 주문 확정 → 현재 세션 내역(SSE). 터치 최적화(≥44px).
- **컴포넌트**: FE-Customer (React/Vite).
- **확장**: PBT-02(장바구니 라운드트립, 클라이언트), RES-10(SSE 재연결 UX).
- **의존**: U2, U3, U4 API/SSE.

### U6. frontend-admin (관리자 UI)
- **책임**: 매장 로그인 → 테이블 그리드 실시간 모니터링(SSE) → 주문 상세/상태 변경/삭제 → 테이블/세션 관리 → 메뉴 관리 → 과거 이력.
- **컴포넌트**: FE-Admin (React/Vite).
- **확장**: RES-10(SSE), SEC(쿠키 기반 세션 UX).
- **의존**: U2, U3, U4 API/SSE.

---

## 요약 표
| 단위 | 유형 | 배포 | 주요 확장 | 의존 |
|------|------|------|-----------|------|
| U1 backend-core | Module | backend | SEC·RES 횡단 | – |
| U2 auth-session | Module | backend | SEC-08/12/14 | U1 |
| U3 menu | Module | backend | SEC-05/08, PBT-03 | U1, U2 |
| U4 order | Module | backend | SEC, PBT-03/04/06/07, RES-10 | U1, U2, U3 |
| U5 frontend-customer | Module | 정적앱 | PBT-02, RES-10 | U2·U3·U4 API |
| U6 frontend-admin | Module | 정적앱 | RES-10, SEC | U2·U3·U4 API |
