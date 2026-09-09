# Business Logic Model — U1 backend-core

**단계**: CONSTRUCTION → Functional Design
**범위**: 횡단 로직(테넌트 스코프·인가·검증·로깅·오류·헬스·백업). 기술 중립.
**스토리**: US-TENANT-01~05

---

## 1. 테넌트 컨텍스트 & 스코프 (US-TENANT-01)
```text
요청 수신
 → 인증 토큰 해석 (관리자 JWT 쿠키 / 고객 세션 토큰)
 → TenantContext 생성 { store_id, role(admin|customer), table_id?, session_id? }
 → 요청 처리 전 컨텍스트 주입(FastAPI 의존성)
데이터 접근
 → TenantScopedRepository: 모든 query에 WHERE store_id = ctx.store_id 강제
 → 서비스 계층: 리소스 반환 전 assert_ownership(resource.store_id == ctx.store_id) 재확인 (이중 방어, Q6=A)
위반 시 → 403 (객체 없음과 구분 없이 일반화 응답, 정보 누출 방지) [SEC-08][SEC-15]
```
**불변식(PBT-03)**: 임의의 (store_A 컨텍스트, store_B 리소스 id) 조합에서 조회/변경은 항상 거부 또는 빈 결과.

## 2. 인가 (Authorization)
- **관리자**: 자기 store 리소스만 CRUD. role=admin 필요한 엔드포인트 가드.
- **고객**: 자기 store+table+session 범위의 조회/주문만. 타 세션 접근 불가.
- 객체 수준 인가는 서비스 진입 시 `assert_ownership` + role 검사.

## 3. 입력 검증 (US-TENANT-02)
- 모든 요청 바디/쿼리는 Pydantic 스키마로 타입·길이·형식 검증. 위반 시 422/400 표준 오류. `[SEC-05]`
- DB 접근은 ORM 파라미터라이즈드(문자열 결합 금지). `[SEC-05]`
- 검증 규칙은 도메인 불변식과 일치(예: price≥0, qty≥1, items 비어있지 않음).
- 퍼징 대상: 도메인 생성기로 검증 견고성 확인. `[PBT-07]`

## 4. 오류 처리 표준 (fail-closed)
```text
- 예상된 도메인 오류 → 명확·일반화 메시지 + 적절한 HTTP 코드
- 인증/인가 실패 → 401/403, 내부 사유 미노출 [SEC-15]
- 예기치 않은 예외 → 500, 상관ID 포함 일반 메시지(스택/내부정보 미노출)
- 기본 동작: 불확실하면 거부(fail-closed)
```

## 5. 구조적 로깅 (US-TENANT-04)
- 각 로그: timestamp(UTC)·correlation_id·level·message·context(store_id 등). `[SEC-03]`
- **마스킹**: password, token, session_token, admin_password_hash 등 민감정보는 로깅 금지/마스킹.
- 보안 이벤트(로그인 실패, 인가 거부, 직권 삭제)는 SECURITY 레벨 + `notify_security_event()` 어댑터 호출. `[SEC-14]`
- **알림 어댑터**(Q8=A): 인터페이스만 정의(`SecurityNotifier`), 기본 구현은 로그 기록. 실제 채널은 추후 연결. `[RES-15]`

## 6. 보안 헤더 & CORS (US-TENANT-03)
- HTML/응답에 CSP·HSTS·X-Content-Type-Options·X-Frame-Options·Referrer-Policy 부여. `[SEC-04]`
- 인증 엔드포인트 CORS: 명시적 허용 오리진 화이트리스트(와일드카드 금지). `[SEC-08]`

## 7. 헬스체크 (US-TENANT-05)
```text
GET /health       → shallow: 프로세스 200 OK
GET /health/deep  → deep: DB 연결 확인(SELECT 1) 등 크리티컬 의존성 점검 [RES-06]
                    실패 시 503
```

## 8. 백업 (US-TENANT-05)
- 스케줄된 `pg_dump`(Q7=A): 주기·보존 정책 문서화, 백업물 암호화. `[RES-12][RES-02]`
- 복원 검증 절차 문서화(DR 전략=Backup & Restore, hours RTO/RPO).
- `run_backup()`는 훅/스크립트로 트리거(상세 스케줄은 Infrastructure Design).

## 9. 공용 리포지토리 베이스
```text
TenantScopedRepository(store_id):
  - list/get/create/update/soft_delete 시 store_id 자동 적용
  - soft_delete: deleted_at = now(UTC), 조회 시 deleted_at IS NULL 필터
  - 총액 등 집계 시 삭제 레코드 제외
```

---

## 스토리 커버리지
| 스토리 | 반영 섹션 |
|--------|-----------|
| US-TENANT-01 | §1 테넌트 스코프, §2 인가 |
| US-TENANT-02 | §3 입력 검증 |
| US-TENANT-03 | §6 헤더/CORS |
| US-TENANT-04 | §5 로깅/알림 |
| US-TENANT-05 | §7 헬스, §8 백업 |
