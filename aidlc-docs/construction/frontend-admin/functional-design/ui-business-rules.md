# U6 frontend-admin — UI Business Rules

Frontend rules for the admin app. Server remains authoritative; these govern UX/state.

| ID | Rule | Story/Ext |
|---|---|---|
| BR-FA01 | 로그인 폼: store_code·admin_username 필수, password 8자 이상(서버 SEC-05와 일치). 미충족 시 제출 비활성. | US-AUTH-01 |
| BR-FA02 | 로그인 성공 시 `store_id`를 localStorage에 저장 → 새로고침에도 로그인 UI 유지(세션은 서버 쿠키 16h). | US-AUTH-02 |
| BR-FA03 | 임의 API가 401을 반환하면 클라이언트 인증 상태를 비우고 `/login`으로 리다이렉트(세션 만료/쿠키 무효 대응). | SEC, US-AUTH-02 |
| BR-FA04 | 반복 로그인 실패(서버 429) 시 서버 메시지를 그대로 노출하고 재시도 안내 — 클라이언트가 우회 재시도하지 않음. | US-AUTH-03, SEC-14 |
| BR-FA05 | 테이블 설정: table_no ≥ 1, table_password 4자 이상. 저장 성공 시 table_id·table_no 확인 메시지. | US-AUTH-04 |
| BR-FA06 | 대시보드는 store 주문을 `table_id`로 그룹핑해 그리드로 표시. 테이블 필터 적용 시 서버 `?table_id=`로 재조회. | US-ORDER-09/12 |
| BR-FA07 | 주문 상세는 항상 `GET /api/orders/{id}`로 최신 items·total을 재조회해 표시(로컬 캐시 신뢰 안 함). | US-ORDER-10 |
| BR-FA08 | 상태 변경은 pending→preparing→done 순 버튼 제공. 서버는 자유 전이 허용이나 UI는 정방향 흐름을 기본 노출. 변경 후 서버 응답으로 상태 확정. | US-ORDER-11, BR-O10 |
| BR-FA09 | 주문 삭제·세션 종료는 확인(confirm) 후 실행. 204 성공 시 목록/그리드에서 반영. | US-SESSION-02/03 |
| BR-FA10 | SSE 이벤트(order_created/status/deleted/session_closed)를 받으면 로컬 그리드를 갱신하되, 재연결·주기적으로 store 목록 전체 재조회로 정합화(누락 방지). | RES-10 |
| BR-FA11 | 메뉴 등록/수정 폼: name(1~100)·price(≥0 정수)·category(1~50) 필수, description≤500, image_url은 http(s):// 로 시작(서버 검증과 일치). | US-MENU-04/05, SEC-05 |
| BR-FA12 | 메뉴 순서 조정은 화면상 순서를 menu_ids 순열로 만들어 `POST /api/menus/reorder`에 전송(전체 순열, BR-M14). | US-MENU-07 |
| BR-FA13 | 메뉴 삭제는 확인 후 `DELETE`(소프트 삭제) → 목록에서 제거. | US-MENU-06 |
| BR-FA14 | 이력 화면은 종료 세션 주문을 읽기 전용으로 표시(변경 액션 없음). | US-SESSION-04 |
| BR-FA15 | 모든 fetch는 `credentials:'include'`; 응답 비-2xx는 사용자에게 오류 메시지로 표면화(무음 실패 금지). | RES-10, SEC |
