# Component Methods — 테이블오더 서비스

**단계**: INCEPTION → Application Design
**범위**: 메서드 시그니처·입출력·상위 목적. **상세 비즈니스 규칙·검증 로직·필드 정의는 Functional Design(Unit별)에서 확정.**
**표기**: 의사 시그니처(언어 중립). 실제 타입/스키마는 구현 단계에서 Pydantic/SQLAlchemy로 구체화.

---

## C1. AuthComponent
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `login(store_code, username, password)` | 자격 정보 | `{admin_token, expires_at}` | 관리자 로그인, JWT 발급 | SEC-12 |
| `logout(admin_token)` | 토큰 | `void` | 세션 무효화 | SEC-12 |
| `verify_admin_token(token)` | JWT | `AdminContext | 401` | 서명·만료·발급자 검증 | SEC-08 |
| `record_login_attempt(store_code, success)` | 시도 결과 | `void` | 실패 누적/잠금 판단 | SEC-12/14 |
| `provision_table(store_id, table_no, table_password)` | 초기 설정 | `TableConfig` | 태블릿 1회 설정 | SEC-12 |
| `auto_login_table(store_code, table_no, table_password)` | 저장 자격 | `{session_token}` | 고객 자동 로그인 세션 | SEC-08 |
| `verify_session_token(token)` | 세션 토큰 | `SessionContext | 401` | 테이블/매장 스코프 검증 | SEC-08 |

## C2. MenuComponent
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `list_menus(store_id, category?)` | 스코프/필터 | `Menu[]` | 카테고리별 조회 | SEC-08 |
| `create_menu(store_id, menu_data)` | 메뉴 필드 | `Menu` | 등록(검증) | SEC-05, PBT-03 |
| `update_menu(store_id, menu_id, changes)` | 변경 | `Menu` | 수정(소유권 확인) | SEC-05/08 |
| `delete_menu(store_id, menu_id)` | 식별 | `void` | 삭제(소유권 확인) | SEC-08 |
| `reorder_menus(store_id, ordered_ids)` | 순서 | `void` | 노출 순서 조정 | SEC-08 |

## C3. OrderComponent
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `place_order(session_ctx, cart_items)` | 장바구니 | `{order_id, order_no, total}` | 주문 확정·총액 계산 | SEC-05, PBT-03 |
| `list_session_orders(session_ctx, paging)` | 세션 | `Order[]` | 현재 세션 내역(고객) | SEC-08 |
| `list_store_orders(store_id, table_no?)` | 스코프/필터 | `Order[]` | 관리자 조회·필터 | SEC-08 |
| `get_order(store_id, order_id)` | 식별 | `Order` | 주문 상세 | SEC-08 |
| `change_status(store_id, order_id, status)` | 상태 | `Order` | 상태 전이 + 이벤트 발행 | SEC-08 |
| `delete_order(store_id, order_id, actor)` | 식별 | `void` | 직권 삭제 + 총액 재계산 | SEC-08/13, PBT-03 |

## C4. SessionComponent
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `get_or_start_session(store_id, table_no)` | 테이블 | `TableSession` | 첫 주문 시 세션 시작 | PBT-06 |
| `close_session(store_id, table_no, actor)` | 테이블 | `{moved_count}` | 이용 완료→이력 이관·리셋 | PBT-04/06 |
| `list_history(store_id, table_no, date_range?)` | 스코프/필터 | `OrderHistory[]` | 과거 이력 조회 | SEC-08 |
| `current_total(store_id, table_no)` | 테이블 | `amount` | 현재 세션 총액 | PBT-03 |

## C5. RealtimeComponent
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `publish(topic, event)` | 토픽/이벤트 | `void` | 이벤트 버스 발행 | SEC-08 |
| `subscribe_customer(session_ctx)` | 세션 | `SSE stream` | 고객 상태 스트림 | RES-10 |
| `subscribe_admin(store_id)` | 매장 | `SSE stream` | 관리자 모니터링 스트림 | RES-10 |
| `resume(stream, last_event_id)` | 재연결 | `SSE stream` | 재연결·복구 | RES-10 |
| `metrics()` | – | `ConnMetrics` | 연결/지연 관측 | RES-05 |

## C6. TenantComponent (횡단)
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `resolve_context(request)` | 요청/토큰 | `TenantContext(store_id, role)` | 테넌트 컨텍스트 결정 | SEC-08 |
| `enforce_scope(query, store_id)` | 쿼리 | 스코프 쿼리 | store_id 강제 필터 | SEC-08, PBT-03 |
| `assert_ownership(store_id, resource)` | 리소스 | `void | 403` | 객체 수준 인가 | SEC-08 |

## C7. PlatformComponent (횡단)
| 메서드 | 입력 | 출력 | 목적 | 확장 |
|--------|------|------|------|------|
| `log_event(level, msg, ctx)` | 로그 | `void` | 구조적 로깅(마스킹) | SEC-03 |
| `notify_security_event(event)` | 이벤트 | `void` | 보안 이벤트 알림 훅 | SEC-14, RES-15 |
| `apply_security_headers(response)` | 응답 | 응답 | 보안 헤더 부여 | SEC-04 |
| `validate_input(payload, schema)` | 입력 | 검증결과 | 공통 입력 검증 | SEC-05, PBT-07 |
| `health(deep=False)` | 플래그 | `HealthStatus` | shallow/deep 헬스체크 | RES-06 |
| `run_backup()` | – | `BackupResult` | DB 백업 훅 | RES-12/02 |

---

> **Note**: 위 시그니처는 상위 계약이며, 입력 검증 규칙·상태 전이 제약·불변식 등 상세는 Functional Design에서 정의합니다.
