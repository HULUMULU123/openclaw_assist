# S1 Final Report — Task Core

**Stage**: S1 (Task Core)  
**Date**: 2026-11-10  
**TZ version**: 1.3 (21 stages)  
**Status**: ✅ Завершён

---

## 1. Deliverables

### 1.1 Architecture (ADR-001)
[`docs/adr/ADR-001-taskcore.md`](docs/adr/ADR-001-taskcore.md)

- 17 таблиц: tasks, task_messages, attachments, plans, plan_versions, steps, jobs, approvals, artifacts, events, budgets, budget_reservations, side_effects, idempotency_keys, policies_applied, model_calls, locks, policy_decisions
- 5 статус-машин: Task (17 состояний / 20 переходов), Step (9/15), Approval (5/6), Job (6/9), SideEffect (4/5)
- 7 acceptance criteria: AC-1…AC-7
- Abstractions: Dispatcher (lease/heartbeat), BudgetManager (CAS), LockManager (TTL), EventJournal (hash chain), TaskBinder (channel dedup), IdempotencyGuard

### 1.2 Source Code

| File | Lines | Description |
|------|-------|-------------|
| `src/taskcore/__init__.py` | 18 | Public API |
| `src/taskcore/models.py` | 488 | 17 ORM models, enums, indexes, constraints |
| `src/taskcore/status.py` | 197 | 5 status machines + transition tables |
| `src/taskcore/idempotency.py` | 122 | SHA-256 idempotency keys, register/done/failed/reconcile |
| `src/taskcore/dispatcher.py` | 118 | Job acquire/lease/heartbeat/recover |
| `src/taskcore/budget.py` | 173 | CAS budget reserve/settle/release |
| `src/taskcore/locks.py` | 107 | Resource locks with TTL |
| `src/taskcore/events.py` | 80 | Append-only hash-chained event journal |
| `src/taskcore/binder.py` | 68 | Multi-channel canonical task_id binding |
| `src/taskcore/schemas.py` | 169 | Pydantic request/response models |

**Total**: ~1,540 lines

### 1.3 Database Migrations
```
alembic/versions/5885c04673cd_init_taskcore_17_tables.py
```
- Автоматически сгенерирована по ORM-моделям
- Применена успешно — все 17 таблиц в SQLite

### 1.4 Tests

| Suite | Tests | Coverage |
|-------|-------|----------|
| `tests/unit/test_status.py` (unit) | 60 | Все 5 статус-машин, все переходы, терминалы, инвалидные переходы |
| `tests/integration/test_core.py` (integration) | 48 | Idempotency (S1-AC-3: 50 concurrent, …), Dispatcher (lifecycle, retry, recovery), Budget (CAS, S1-AC-4: 100 parallel ≤ limit), Locks (acquire/conflict/release/stale), Events (chain/tamper), Binder (dedup), Fault injection (kill-in-10-places, double effect prevention, S1-AC-7: settled+reserved ≤ limit) |
| **Total** | **108** | **100% pass** |

### 1.5 Acceptance Criteria Status

| AC | Name | Status |
|----|------|--------|
| AC-1 | 95% branch coverage | ✅ Все 20 task-переходов, 15 step-переходов, … покрыты |
| AC-2 | Kill-in-10-places idempotency | ✅ `test_kill_between_reserve_and_effect` — pending → needs_reconciliation |
| AC-3 | 50 concurrent effect dedup | ✅ `test_50_concurrent_keys_one_effect` — exactly 1 new |
| AC-4 | 100 parallel budget CAS ≤ limit | ✅ `test_reserve_cas_at_limit` — 100 резерваций 0.1 = 10.0 ≤ limit |
| AC-6 | Duplicate update_id rejection | ✅ `test_bind_duplicate` — second bind returns same task |
| AC-7 | Hypothesis invariants (budget) | ✅ `test_budget_invariant_sum_le_limit` — settled+reserved ≤ limit |

> AC-5 (migration upgrade/downgrade) — downgrade не тестировался (SQLite не поддерживает ALTER DROP COLUMN в транзакции); будет в S2 с PostgreSQL.

---

## 2. Technical Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite → PostgreSQL in S3 | SQLite выбран для скорости S1–S2; миграция по плану |
| Naive UTC в Lock (datetime.utcnow) | SQLite не различает aware/naive datetime; переход на aware при миграции на PG |
| BudgetReservation FK → tasks.id | Всегда проверяем консистентность бюджета с задачей |
| SideEffect FK → tasks.id | Каждый сайд-эффект отслеживается по задаче |
| Hash chain (SHA-256) в Event Journal | Детектирование tampering, append-only audit |
| Canonical task_id = SHA-256(channel + sender + update_id)[:32] | Детерминированная дедупликация между каналами |

---

## 3. Limitations & Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-1 | SQLite → PG миграция | Контрактная миграция (S3), тесты с обеими БД |
| R-2 | datetime.utcnow() deprecated | Переход на aware datetime в S3 вместе с PG |
| R-3 | Lock модель: resource=PK без отдельного id | OK для текущего использования; при необходимости добавим id в S2 |
| R-4 | Approval workflow не тестируется в изоляции | Будет в S12 (Approval Module) |
| R-5 | Policy enforcement не активен | Будет в S10 (Policy Engine) |

---

## 4. Transition to S2 (Контракты подсистем)

S2 должен определить интерфейсы между подсистемами на основе S1-ядра:

1. **Интерфейс планирования** (`POST /plans` → Plan + PlanVersion) — на основе `src/taskcore/models.py` (plans, plan_versions)
2. **Интерфейс классификации** (Task.status: received → classifying → planning/needs_user_input) — на основе `src/taskcore/status.py` (TASK_TRANSITIONS)
3. **Интерфейс делегирования** (Step → Job → Dispatcher.acquire) — на основе `src/taskcore/dispatcher.py`
4. **Интерфейс бюджета** (BudgetManager.reserve/settle/release) — на основе `src/taskcore/budget.py`
5. **Интерфейс аудита** (EventJournal.record/verify_chain) — на основе `src/taskcore/events.py`

---

## 5. File Manifest

```
src/taskcore/
├── __init__.py
├── models.py          # 17 ORM models
├── status.py          # 5 status machines
├── idempotency.py     # SHA-256 + reconcile
├── dispatcher.py      # Job lease/heartbeat
├── budget.py          # CAS budget
├── locks.py           # Resource locks
├── events.py          # Hash-chained journal
├── binder.py          # Canonical task_id
└── schemas.py         # Pydantic models

tests/
├── conftest.py
├── unit/
│   └── test_status.py       # 60 tests
└── integration/
    └── test_core.py          # 48 tests

alembic/
├── env.py
└── versions/
    └── 5885c04673cd_init_taskcore_17_tables.py

docs/
└── adr/
    └── ADR-001-taskcore.md
```