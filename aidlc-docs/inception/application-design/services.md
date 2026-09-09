# Services — 테이블오더 서비스

**단계**: INCEPTION → Application Design
**패턴**: Service Layer가 오케스트레이션을 담당하고, Repository Layer(테넌트 스코프)를 통해 DB에 접근. 실시간은 인메모리 이벤트 버스(RealtimeService) 경유.

---

## 서비스 목록 및 책임

### S1. AuthService
- **책임**: 관리자 인증 흐름, 테이블 프로비저닝, 고객 자동 로그인 세션 발급, 토큰 검증.
- **오케스트레이션**:
  - `login`: StoreRepository 조회 → bcrypt 검증 → 시도 기록(AuthAttempt) → JWT 발급.
  - `auto_login_table`: Table/TableSession 조회·검증 → 세션 토큰 발급.
- **의존**: StoreRepository, TableRepository, TableSessionRepository, PlatformService(로깅/알림), TenantContext.

### S2. MenuService
- **책임**: 메뉴 CRUD·정렬·조회 오케스트레이션, 입력 검증.
- **오케스트레이션**: 요청 → TenantContext 스코프 확인 → 검증 → MenuRepository 반영 → (변경 시) RealtimeService로 메뉴 갱신 이벤트(선택).
- **의존**: MenuRepository, TenantComponent, PlatformService(검증/로깅).

### S3. OrderService
- **책임**: 주문 확정·조회·상태 전이·삭제, 총액 계산, 실시간 이벤트 발행.
- **오케스트레이션**:
  - `place_order`: 세션 컨텍스트 검증 → SessionService.`get_or_start_session` → 장바구니 검증·총액 계산 → OrderRepository 생성 → RealtimeService.publish(admin 토픽).
  - `change_status` / `delete_order`: 소유권 확인 → 반영 → RealtimeService.publish(customer+admin 토픽) → (삭제) 감사 로깅.
- **의존**: OrderRepository, SessionService, RealtimeService, TenantComponent, PlatformService.

### S4. SessionService
- **책임**: 세션 라이프사이클, 이용 완료 이관, 이력 조회, 현재 총액.
- **오케스트레이션**:
  - `close_session`: 활성 세션 조회(멱등) → 주문 OrderHistory 이관 → 세션 종료·완료시각 기록 → 총액 리셋 → RealtimeService.publish.
- **의존**: TableSessionRepository, OrderRepository, OrderHistoryRepository, RealtimeService, TenantComponent.

### S5. RealtimeService
- **책임**: 인메모리 이벤트 버스와 SSE 스트림 관리(토픽=store/table 스코프), 재연결·메트릭.
- **오케스트레이션**: publish → 토픽 구독자 큐에 push → SSE 제너레이터가 클라이언트로 전송. 하트비트/타임아웃/Last-Event-ID 재개.
- **의존**: (인메모리) 없음 외부. TenantComponent(구독 스코프 검증), PlatformService(메트릭/로깅).

### S6. PlatformService (횡단)
- **책임**: 로깅, 보안 이벤트 알림, 입력 검증 유틸, 보안 헤더/CORS, 헬스체크, 백업 훅.
- **오케스트레이션**: FastAPI 미들웨어/의존성으로 전 요청에 적용. 헬스/백업은 별도 엔드포인트/스케줄.
- **의존**: DB(헬스 deep·백업), 로깅 인프라.

---

## 서비스 오케스트레이션 다이어그램 (주요 흐름)

### 주문 확정 (US-ORDER-05)
```text
FE-Customer ─POST /orders─▶ OrderService
   OrderService → TenantComponent.resolve/assert(session scope)
   OrderService → SessionService.get_or_start_session()
   OrderService → 검증+총액계산 → OrderRepository.create()
   OrderService → RealtimeService.publish(store:{id} admin 토픽)
                         └─SSE─▶ FE-Admin (신규 주문 2초 내)
   OrderService ─{order_no,total}─▶ FE-Customer
```

### 상태 변경 (US-ORDER-11 / US-ORDER-08)
```text
FE-Admin ─PATCH /orders/{id}/status─▶ OrderService
   OrderService → TenantComponent.assert_ownership()
   OrderService → OrderRepository.update_status()
   OrderService → RealtimeService.publish(customer 세션 토픽 + admin 토픽)
                         ├─SSE─▶ FE-Customer (상태 갱신)
                         └─SSE─▶ FE-Admin (그리드 갱신)
```

### 이용 완료/세션 종료 (US-SESSION-03)
```text
FE-Admin ─POST /tables/{id}/close-session─▶ SessionService
   SessionService → 활성 세션 조회(멱등)
   SessionService → OrderHistoryRepository.move(session orders)
   SessionService → TableSessionRepository.close() (완료시각)
   SessionService → RealtimeService.publish(admin 토픽: 테이블 리셋)
   SessionService ─{moved_count}─▶ FE-Admin
```

---

## 확장 규칙 매핑 (서비스 관점)
- **보안**: 모든 서비스는 TenantComponent로 스코프/소유권 강제(SEC-08), PlatformService로 검증(SEC-05)·로깅(SEC-03)·헤더(SEC-04)·오류(SEC-15).
- **복원력**: RealtimeService 재연결/타임아웃(RES-10), PlatformService 헬스체크(RES-06)·백업(RES-12/02)·관측성(RES-05).
- **PBT**: OrderService/SessionService의 총액·세션·격리 불변식(PBT-03/04/06), 검증 퍼징(PBT-07).
