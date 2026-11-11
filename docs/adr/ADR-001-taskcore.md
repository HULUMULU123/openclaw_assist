# ADR-001: Архитектура Task Core

**Статус:** принято | **Дата:** 10.11.2026 | **Версия:** 1.0

## Контекст

Task Core — независимое ядро управления задачами. Взаимодействие с OpenClaw — через отдельный адаптер. Стек: Python 3.13, FastAPI, SQLAlchemy 2, Alembic, SQLite, Pydantic 2, pytest.

## Решение

### 1. Схема БД (17 таблиц)

```
tasks ──────────────< task_messages
  │                    └─ attachments
  ├──< plans ──< plan_versions
  ├──< steps ──< jobs
  ├──< approvals
  ├──< artifacts
  ├──< events (append-only)
  ├──< side_effects ──< idempotency_keys
  ├──< policies_applied
  ├──< model_calls
  ├──< budget_reservations
  ├──< locks
  └──< policy_decisions
```

### 2. Статус-машины

**Task:** `received → classifying → needs_user_input ↔ planning → awaiting_approval → running → verifying → succeeded | failed | cancelled | paused | blocked_*`

**Step:** `pending → ready → running → verifying → succeeded | failed | needs_evidence | needs_reconciliation | skipped`

**Approval:** `pending → approved | rejected | expired | invalidated`

**Job:** `queued → leased → running → done | failed | expired`

**SideEffect:** `pending → done | failed | needs_reconciliation`

### 3. Ключевые абстракции

| Компонент | Ответственность |
|---|---|
| `StatusMachine` | Валидация переходов, enum статусов |
| `IdempotencyGuard` | Ключ = hash(task_id, step_id, effect_type, canonical_args); CAS-запись |
| `Dispatcher` | Lease/heartbeat/timeout; восстановление зависших jobs |
| `BudgetManager` | reserve → call → settle/release; CAS; лимиты |
| `LockManager` | Блокировки ресурсов с владельцем и TTL |
| `EventJournal` | Append-only журнал с хеш-цепочкой |
| `TaskBinder` | Канонический task_id для multi-channel |

### 4. Правила

- **Единственный writer** для каждой задачи
- **Idempotency:** pending side_effect → needs_reconciliation при рестарте, НЕ автоповтор
- **Deny-by-default** для неизвестных действий
- **LOCAL_ONLY** метка для данных, не покидающих контур
- **Budget CAS:** атомарный reserve без нарушения лимита

### 5. Тестовый контракт

- S1-AC-1: 95% покрытия ветвей статус-машин
- S1-AC-2: kill в 10 точках «reserve → effect → settle» → нет двойного эффекта
- S1-AC-3: 50 конкурентных подтверждений → ровно 1 эффект
- S1-AC-4: 100 параллельных резервов бюджета ≤ лимит
- S1-AC-5: upgrade/downgrade миграций без потери данных
- S1-AC-6: повторный update_id → нет дубля задачи
- S1-AC-7: инварианты (hypothesis): сумма settled+reserved ≤ лимит

### 6. Структура пакета

```
src/taskcore/
├── __init__.py
├── models.py          # SQLAlchemy ORM модели
├── status.py          # Статус-машины (Enum + таблицы переходов)
├── idempotency.py     # Идемпотентность
├── dispatcher.py      # Lease/heartbeat диспетчер
├── budget.py          # Бюджет (CAS)
├── locks.py           # Блокировки ресурсов
├── events.py          # Append-only журнал
├── binder.py          # Канонические task_id
├── api.py             # FastAPI роуты
└── schemas.py         # Pydantic схемы
```

## Последствия

- Task Core можно тестировать изолированно, без OpenClaw
- Адаптер OpenClaw — точка интеграции, не ядро
- Миграции Alembic обеспечивают версионирование схемы
- SQLite выбран для простоты локальной разработки; замена на PostgreSQL — замена connection string