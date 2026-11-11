# OpenClaw v2 — Контекст проекта

**Версия:** 0.1-dev | **Дата:** 11.11.2026 | **Фаза:** S2 (Policy / контракты подсистем) | **ТЗ:** v1.4

## Что это

Локальный универсальный ИИ-помощник на базе OpenClaw. Один оркестратор принимает задачи через Telegram/веб-панель, классифицирует, планирует, делегирует субагентам, проверяет результат. Целевая платформа: HP Pavilion (Windows 11 + WSL2, 16 ГБ RAM / 512 ГБ SSD). Разработка на macOS (Apple Silicon, 24 ГБ).

**Стек:** Python 3.13, FastAPI, SQLAlchemy 2, Alembic, SQLite, Pydantic 2, pytest.

**Архитектурное решение:** Task Core независим от OpenClaw. Взаимодействие через отдельный адаптер с чёткими интерфейсами. Без дублирования штатных функций OpenClaw.

**⚠️ Сетевое ограничение HP:** ноутбук находится за роутером, доступ к которому возможен только через VPN. Без VPN ноутбук не может выходить в интернет к API провайдеров LLM (DeepSeek, MiniMax, Qwen, …). Поэтому **VPN должен быть установлен как автоматическая служба** (Windows Service / systemd в WSL2), запускающаяся при старте системы до инициализации агента. Без этого любой вызов внешней модели завершится ошибкой сети.

## Текущий статус

- **S0:** ✅ инвентаризация, структура, навыки, вопросы решены (U-02/04/05/06/07)
- **S1:** ✅ завершён — ADR-001, 17 таблиц, 5 статус-машин, 108 тестов, отчёт [`docs/reports/S1-report.md`](docs/reports/S1-report.md)
  → Новые задачи из v1.4: S0-T8, S0B-T5, S0B-T6 (см. STATUS.md)

## Ключевые решения (10–11.11.2026)

| Решение | Описание |
|---|---|
| Task Core — отдельно | Независим от OpenClaw; адаптер OpenClaw — отдельный слой |
| Стек | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, SQLite, Pydantic 2, pytest |
| Модели | S1–S2 на Mock LLM; ключи позже через локальное хранилище |
| Windows | Адаптеры через mock + контрактные тесты; реальные испытания на HP позже |
| Безопасность | Изоляция, синтетические данные, без реальных аккаунтов/админ-прав |

### Новые решения (v1.4, 11.11.2026)

| Решение | Источник | Описание |
|---|---|---|
| **LLM Gateway** | `16` §3.2 | Единственный путь сторонних проектов к LLM: loopback OpenAI-совместимый endpoint, эфемерный ключ на job |
| **Adapter contract** | `16` §3.1 | Единый контракт интеграции стороннего проекта + тест-набор соответствия (S7) |
| **Профили AG-00…AG-11** | `16` §2 | 12 LLM-профилей: `quarantine-reader` (AG-00), `classifier-light` (AG-01), `planner` (AG-02), …, `windows-companion` (AG-08), `research` (AG-04), `calc` (AG-05), `cad` (AG-06), `scribe` (AG-07), `proofreader` (AG-09), `instructor` (AG-10), `multimodal-explorer` (AG-11) |
| **«Правило двух»** | `16` §2.2 | GUI-агент = экран + приложения + действия. Комбинация A+B+C (open) запрещена без пошагового approval |
| **Граница доверия Windows** | `16` §3.3 | Windows Companion с COM-доступом к Office — наибольшая привилегия; варианты изоляции |
| **Цепочка поставки навыков** | `16` §3.5 | Вендоринг в `skills/vendor/`, хеши SHA-256, ревью `SKILL.md`, закрепление описаний MCP-инструментов |
| **Ворота G1–G7** | `16` §7.1 | Жёсткие ворота для каждого кандидата: лицензия, телеметрия, base_url, sandbox, зависимости, активность, размер |
| **Дорожная карта по зависимостям** | `16` §8.2 | A (S0–S3, S17-min, Gateway) → B (S4–S7, Adapter) → C (S11, S9, S10) → D (S8, S12) → E (S14, S13); S15, S17–S21 сквозные; S16 последним |
| **Статус `claimed`** | `16` §10 | До S0B-T5 все проекты — `claimed` (заявлено, не проверено) |
| **Ворота диплома** | `16` §7.2, поправки §2.17 | Академическая добросовестность и инженерная ответственность (S14-AC-6) |
| **§6D RAG + S22** | поправки v1.4 | Гибридный FTS5+vector, родитель-дочерние чанки, уровни L-A…L-D, русская токенизация; ADR-K (эмбеддинги), ADR-L (реранкер); embedding endpoint на Gateway |
| **Harness²** | `third-party.md` §4.10, `16` §4.11 | Рекурсивная обвязка агента: референс для S21 + изолированный S15; жесткие ограничения; ADR-M |
| **Obscura** | `third-party.md` §4.1a, `16` §4.2 | Лёгкий read-only headless-браузер (Rust, собственный движок+V8, CDP); 4-й уровень лестницы S8; ADR-N |

## Ключевые документы

| Документ | Путь |
|---|---|
| ТЗ архитектура | `../Релейная защита/01-ТЗ-Архитектура-и-требования.md` |
| ТЗ разработчика v1.3 | `../Релейная защита/15-ТЗ-для-агента-разработчика (1).md` |
| **Поправки v1.4** | [`docs/15-ТЗ-поправки-v1.4.md`](docs/15-ТЗ-поправки-v1.4.md) |
| **Архитектура субагентов v0.2** | [`docs/16-Архитектура-субагенты-навыки-интеграции-v0.2.md`](docs/16-Архитектура-субагенты-навыки-интеграции-v0.2.md) |
| Модели/маршрутизация | `../Релейная защита/14-Модели-маршрутизация-MiniMax-Jev.md` |
| Навыки агента | `../Релейная защита/15-Навыки-агента-разработчика.md` |
| Навыки OpenClaw | `../Релейная защита/16-Навыки-и-MCP-готового-OpenClaw.md` |
| Реестр навыков | `src/skills/REGISTRY.md` |
| Статус | `STATUS.md` |
| Открытые вопросы | `docs/open-questions.md` |

## Окружение разработки

- **ОС:** macOS 25.6 (Darwin ARM64)
- **CPU:** 10 ядер (Apple M-series)
- **RAM:** 24 ГБ
- **Диск:** 460 ГБ (85 ГБ свободно)
- **Python:** 3.13.7
- **Node.js:** 26.12.1, npm 11.20.0, pnpm
- **БД:** SQLAlchemy 2.0.52 + Alembic 1.19.1
- **Pydantic:** 2.13.4
- **Git:** 2.39.5
- **Docker:** отсутствует
- **OpenClaw:** не установлен

## Структура проекта

```
OpenClaw_v2/
├── src/
│   ├── taskcore/        # S1: ядро задач, БД, статус-машины
│   ├── policy/          # S2: Policy Engine, согласования
│   ├── orchestrator/    # S6: оркестратор, делегирование
│   ├── router/          # S4: маршрутизация моделей + LLM Gateway (S4-T10)
│   ├── adapters/        # S5,S8,S9,S11,S13: адаптеры каналов/программ
│   │   └── gateway/     # S4-T10: LLM Gateway (loopback, совместимый с OpenAI)
│   ├── skills/          # Навыки агента-разработчика
│   │   └── vendor/      # v1.4: вендоренные сторонние навыки (с хешами)
│   └── web/             # S10: веб-панель
├── tests/
│   ├── unit/            # Модульные тесты
│   ├── integration/     # Интеграционные
│   ├── fault/           # Fault injection (S1-T8)
│   ├── security/        # Тесты безопасности (S2-T8)
│   └── conformance/     # S7-T10: Adapter contract conformance tests
├── docs/
│   ├── adr/             # Архитектурные решения
│   ├── reports/         # Отчёты
│   ├── design/          # Проектная документация
│   ├── 15-ТЗ-поправки-v1.4.md
│   └── 16-Архитектура-субагенты-навыки-интеграции-v0.2.md
├── config/policy/       # Правила Policy Engine (S2-T3)
├── scripts/             # Установка, backup, restore
├── eval/                # S15: evaluation suite
├── knowledge/           # База знаний (S21)
└── data/                # Тестовые данные
```

## Правила работы

1. **Навыки:** применять по задаче, не все сразу. P0-навыки superpowers — на каждом этапе.
2. **Словарь статусов (ТЗ §12.7):** «реализовано» = код + тесты; «работает» = критерии приёмки + живое подтверждение.
3. **Конфликты:** приоритет у поправок v1.4 над текстом v1.3 до их переноса в основной текст. При конфликте → `docs/open-questions.md`.
4. **Безопасность:** deny-by-default, LOCAL_ONLY для чувствительных данных. Цепочка поставки навыков (`16` §3.5). Сторонние проекты — только через LLM Gateway (`16` §3.2).
5. **Сначала тест, потом код** (TDD).
6. **Статусы внешних проектов** (`16` §10): `claimed` → `documented-verified` → `tested_in_sim` → `tested_live` → `tested_target`. До S0B-T5 все — `claimed`.
7. **Профили LLM** (`16` §2): 12 профилей AG-00…AG-11. `quarantine-reader` (AG-00) — обязательный, без инструментов. «Правило двух» для GUI-агента.
8. **Ворота G1–G7** (`16` §7.1): ни один кандидат не включается без их прохождения или записи об исключении.

## Навыки и субагенты (11.11.2026)

**Среда:** DSH (DeepSeek Harness). Навыки загружаются из `~/.agents/skills/` (162 шт.) через `skill()`.

### Покрытие запрошенных навыков: 50/50 = 100%

| Источник | Запрошено | Установлено | Статус |
|---|---|---|---|
| obra/superpowers | 12 | 12 ✅ | `~/.agents/skills/` |
| anthropics/skills | 3 | 3 ✅ | каталог DSH |
| vercel-labs | 1 | 1 ✅ | `vercel-react-best-practices` |
| trailofbits/skills | 9 | 9 📥 | `/tmp/trailofbits-skills/` (.mdc, нужна адаптация) |
| wshobson/agents | 18 | 18 📥 | `/tmp/wshobson-agents/` (референс профилей) |
| VoltAgent | 7 | 7 📥 | `/tmp/voltagent-subagents/` (референсы) |

### Ключевые навыки для разработки

**P0 (обязательные):** `brainstorming`, `writing-plans`, `subagent-driven-development`, `dispatching-parallel-agents`, `executing-plans`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `using-git-worktrees`, `finishing-a-development-branch`

**P0 (безопасность):** `spec-to-code-compliance` (trailofbits, .mdc), `security-and-hardening` (DSH), `code-review-and-quality` (DSH)

**P0 (инструменты):** `mcp-builder`, `skill-creator`, `webapp-testing`, `vercel-react-best-practices`

**P1 (субагенты):** профили из wshobson/agents как шаблоны для DSH `subagent`/`subagent_fork`

### Модель делегирования

Lead Developer → Planning → Specialized Workers → Independent Review → Integration → Verification. Подробнее: [`docs/delegation-principles.md`](docs/delegation-principles.md).

**Ограничения:** ≤3 параллельных субагента, изоляция через worktrees, ревьюер ≠ автор, подтверждение тестами.

### Карта покрытия

Полная карта: [`docs/skills-coverage.md`](docs/skills-coverage.md). Реестр: [`src/skills/REGISTRY.md`](src/skills/REGISTRY.md).