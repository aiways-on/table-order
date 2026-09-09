# AI-DLC State Tracking

## Project Information
- **Project Name**: Table-Order Service (테이블오더 서비스)
- **Project Type**: Greenfield
- **Start Date**: 2026-09-07T03:18:02Z
- **Current Phase**: CONSTRUCTION
- **Current Stage**: U5 frontend-customer — COMPLETE (Functional Design + Code Generation; 18 FE tests pass, build OK). All 6 units (U1-U6) COMPLETE. Next: Build and Test (final integration across all units).

## Workspace State
- **Existing Code**: No
- **Programming Languages**: None detected
- **Build System**: None detected
- **Project Structure**: Empty (greenfield) — only requirements docs + AI-DLC setup
- **Reverse Engineering Needed**: No
- **Workspace Root**: /Users/suntae/table-order

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Input Requirements Documents
- requirements/table-order-requirements.md (서비스 요구사항 정의서)
- requirements/constraints.md (구현 예외사항)

## Extension Configuration
| Extension | Enabled | Mode | Decided At |
|---|---|---|---|
| Security Baseline | Yes | Full (all SECURITY-01..15 blocking) | Requirements Analysis |
| Property-Based Testing | Yes | Full (all PBT-01..10 blocking) | Requirements Analysis |
| Resiliency Baseline | Yes | Full (all RESILIENCY-01..15 blocking) | Requirements Analysis |

**Note**: Resiliency opt-in triggers mandatory user-decision questions (RESILIENCY-02 RTO/RPO+DR, RESILIENCY-03 change management, RESILIENCY-15 incident response) that MUST be answered during Requirements. RESILIENCY-04/08/14 decisions deferred to NFR Design.

### Requirements Answers (round 1)
- Q1 Multi-tenancy: A — Multi-tenant (다중 매장, 매장 식별자로 구분)
- Q2 Backend: A — Python (FastAPI)
- Q3 Frontend: A — React (Vite + React)
- Q4 Database: A — Relational (PostgreSQL/MySQL)
- Q5 Deployment target: A — Local dev focus (docker-compose, demo/learning)
- Q6 Scale: A — Small (per-store few~dozens of tables, demo/MVP)
- Q7 Menu image: A — Image URL only (no upload)
- Q8 Customer real-time order status: A — Included (customer screen also SSE)
- Q9 Security ext: A — Yes (enforce all)
- Q10 PBT ext: A — Yes (enforce all)
- Q11 Resiliency ext: A — Yes (apply baseline)

**Noted tension (non-blocking)**: Q5/Q6 (local demo/MVP, small scale) vs Q9/Q10/Q11 (full production-grade extensions). Coherent for a learning/workshop context; extensions add engineering rigor. Documented in requirements.md; proceeding per explicit user instruction ("모두 A").

## Stage Progress
- [x] INCEPTION - Workspace Detection (Greenfield confirmed) — 2026-09-07T03:18:02Z
- [x] INCEPTION - Requirements Analysis (approved) — 2026-09-07T03:18:02Z
- [x] INCEPTION - User Stories (approved: personas.md + stories.md [33 stories, 5 Epics]) — 2026-09-08T00:05:00Z
- [x] INCEPTION - Workflow Planning (approved: execution-plan.md) — 2026-09-08T00:20:00Z
- [x] INCEPTION - Application Design — EXECUTE (approved; 5 artifacts, 7 components; decisions Q1-Q6 all A) — 2026-09-08T00:35:00Z
- [x] INCEPTION - Units Generation — EXECUTE (approved; 6 units, 33 stories mapped) — 2026-09-08T00:55:00Z
- **INCEPTION PHASE COMPLETE** → CONSTRUCTION PHASE (per-unit loop over U1-U6)
- **Construction pacing**: 단위별 순차 + 승인 (per-unit sequential with approval gates)

### 🟢 CONSTRUCTION PHASE — Per-Unit Progress
- [x] **U1 backend-core — COMPLETE** (all CONSTRUCTION stages). Functional Design [x]; NFR Requirements [x] generated (Q1-Q7 all A: p95<300ms/SSE<2s, single-instance dozens sessions, Backup&Restore hours RTO/RPO, unit+Hypothesis 80%+, structured logging+metrics+health, .env secrets, bcrypt/JWT local-HTTP) — [x] approved; NFR Design [x] generated (Q1-Q7 all A: timeout+bounded-retry+fail-closed, composite-index+pool+pagination no-cache, single-instance/single-region + documented scale-out path [RES-08], layered middleware+central exception handler, tag-based deploy + Alembic downgrade rollback [RES-04], backup/restore rehearsal + DB-down/graceful-shutdown tests [RES-14], core-consolidated logical components) — RES-04/08/14 finalized [x] approved; Infrastructure Design [x] generated (Q1-Q7 all A: local docker-compose single env, single uvicorn container, postgres:16 + named volume + pg_dump backup service, in-memory event bus, internal compose net no LB, stdout logs + /health + /metrics, single-DB shared-schema store_id; shared-infrastructure.md created) [x] approved; Code Generation [x] Part 1 plan approved + Part 2 generated (backend/ scaffolding + app/core 12 modules + app/shared models/repository/schemas + main.py + tests[14 passed incl Hypothesis PBT] + Alembic 0001 migration + Dockerfile/entrypoint/docker-compose/backup.sh + code-summary.md; US-TENANT-01~05 [x]) — [x] approved → U2 auth-session
- [~] U2 auth-session (consumes app/core + app/shared from U1) — adaptive stages: Functional Design (EXECUTE) + Code Generation (EXECUTE); NFR Requirements/NFR Design/Infrastructure Design SKIPPED (cross-cutting NFRs, patterns & shared infra already fixed in U1). Functional Design [x] approved (Q1-Q7 all A: store_code+username login, cookie-delete logout, acct+IP rate-limit, secrets session token 16h, 1 active session/table, client-stored auto-login, bcrypt 12; auth-logic-model.md + auth-business-rules.md BR-A01~A20). Code Generation [x] Part 1 plan approved + Part 2 generated (app/auth: security/schemas/service/dependencies/router + main.py wiring; U1 errors.py bug fix [logger message→detail]; bcrypt<4.1 pin; tests[**38 passed** = U1 14 + U2 24, incl Hypothesis PBT BR-A18/A19/A20]; code-summary.md; US-AUTH-01~05 [x]) — [x] approved → U3 menu. **U2 COMPLETE.**
- [~] U3 menu (consumes app/core + app/shared[Menu] + auth guards from U1/U2) — adaptive stages: Functional Design (EXECUTE) + Code Generation (EXECUTE); NFR Requirements/NFR Design/Infrastructure Design SKIPPED (cross-cutting fixed in U1). Functional Design [x] generated (Q1-Q7 all A: category-as-string/no new table, soft-delete only [no is_available], bulk-reorder API, soft delete, category-grouped customer list + single GET, SEC-05 standard validation, read=customer|admin & write=admin-only + IDOR dual-defense; menu-logic-model.md + menu-business-rules.md BR-M01~M20, PBT invariants BR-M15~M18) — [x] approved. Code Generation [x] Part 1 plan approved + Part 2 generated (app/menu: schemas/repository/service/router + main.py wiring; context-thread-propagation fix [each endpoint re-asserts set_context(ctx) in its own threadpool worker]; tests[**57 passed** = U1 14 + U2 24 + U3 19, incl Hypothesis PBT BR-M15~M18]; code-summary.md; US-MENU-01~07 [x]) — [x] approved → U4 order. **U3 COMPLETE.**
- [~] U4 order (Order + Session lifecycle-on-order + Realtime SSE; US-ORDER-01~12, US-SESSION-01~04; consumes U1 core[events/eventbus, models Order/TableSession/OrderHistory] + U2 auth guards + U3 MenuService) — adaptive stages: Functional Design (EXECUTE) + Code Generation (EXECUTE); NFR Requirements/NFR Design/Infrastructure Design SKIPPED (cross-cutting fixed in U1; SSE/event-bus built in U1). Functional Design [x] generated (Q1-Q7 all A: per-session sequential order_no, server-refetched price snapshot [ignore client prices], SSE 2-topic store:{id}[admin cookie]+session:{id}[customer ?token=], enum-validated free status transitions, session close→OrderHistory copy+soft-delete, order soft-delete+total recompute+SSE, customer=own-session/admin=store-wide isolation; order-logic-model.md + order-business-rules.md BR-O01~O19, PBT invariants BR-O15~O19) — [x] approved. Code Generation [x] Part 1 plan approved + Part 2 generated (app/order: schemas/repository/events/service/sse/router + main.py wiring [order_router + event_bus.attach_loop in lifespan] + app/core/events.py extended [publish_sync/attach_loop for sync-path SSE]; customer SSE endpoint fixed to Depends(get_db) [was raw SessionLocal → untestable/blocked on real PG]; **no new DB tables/migration** [U1 Order/TableSession/OrderHistory reused]; tests[**82 passed** = U1 14 + U2 24 + U3 19 + U4 25: service 8 + properties 5 Hypothesis BR-O15~O19 + API 12]; code-summary.md; US-ORDER-05~12 + US-SESSION-01~04 [x]) — verified in throwaway venv (py3.13, bcrypt 4.0.1), venv removed. **U4 COMPLETE** → awaiting gate → U5.
- [x] **U5 frontend-customer — COMPLETE** (consumes U2 auth session-token + U3 menu + U4 order/SSE APIs). Adaptive stages: Functional Design [x] (ui-flow-model.md + ui-business-rules.md BR-FC01~15) + Code Generation [x] (frontend-customer/ React+Vite app: api/client[X-Session-Token header + `{error:{message}}` parsing]+auth+menus+orders, SessionContext[localStorage auto-login US-AUTH-05]+CartContext[local cart persist US-ORDER-01~04], useOrderStream SSE `?token=`, SessionRoute+AppLayout, pages Start/Menu/Orders, index.css, Dockerfile+nginx.conf; docker-compose frontend-customer service :5173; US-AUTH-05, US-MENU-01/02/03, US-ORDER-01~08 [x]); NFR Requirements/NFR Design/Infrastructure Design SKIPPED (cross-cutting fixed in U1). Verified: `npm test` **18 passed** (4 files), `npm run build` OK. Extensions: SEC(token header/401-clear/client-price-untrusted/session-isolation) + RES-10(SSE reconnect+REST resync) compliant, PBT N/A (backend invariants). **U5 COMPLETE.** 2026-09-08
- [x] **U6 frontend-admin — COMPLETE** (consumes U2 auth cookie + U3 menu + U4 order/SSE APIs). Adaptive stages: Functional Design [x] (ui-flow-model.md + ui-business-rules.md BR-FA01~15; design Q1-Q3 all recommended: react-router+Context/hooks, EventSource+resync, Vite proxy+docker-compose nginx) + Code Generation [x] (frontend-admin/ React+Vite app: api/client+auth+menus+orders, AuthContext, useOrderStream SSE, ProtectedRoute+AppLayout, pages Login/Dashboard/Menus/Tables/History, index.css, Dockerfile+nginx.conf; docker-compose frontend-admin service :5174; US-AUTH-01~04, US-MENU-04~07, US-ORDER-09~12, US-SESSION-02~04 [x]); NFR Requirements/NFR Design/Infrastructure Design SKIPPED (cross-cutting fixed in U1). Verified: `npm test` **11 passed**, `npm run build` OK. Extensions: SEC + RES-10 compliant, PBT N/A (U5 scope). Auto-approved per user ("무조건 승인").
- [ ] Build and Test (after all units)
- [ ] CONSTRUCTION - Functional Design — EXECUTE
- [ ] CONSTRUCTION - NFR Requirements — EXECUTE
- [ ] CONSTRUCTION - NFR Design — EXECUTE
- [ ] CONSTRUCTION - Infrastructure Design — EXECUTE
- [ ] CONSTRUCTION - Code Generation — EXECUTE
- [ ] CONSTRUCTION - Build and Test — EXECUTE

## Execution Plan Summary
- **Stages to Execute**: Application Design, Units Generation, Functional Design, NFR Requirements, NFR Design, Infrastructure Design, Code Generation, Build and Test
- **Stages Skipped**: Reverse Engineering (greenfield)
- **Risk Level**: Medium | **Rollback**: Easy | **Testing**: Complex
- **Tentative Units**: backend-core, auth-session, menu, order, frontend-customer, frontend-admin (finalized in Units Generation)
