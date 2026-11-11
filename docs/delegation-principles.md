# Принципы делегирования работы в OpenClaw v2

**Дата:** 11.11.2026 | **Источник:** задание владельца §7 + `16-Архитектура` v0.2 | **Референс:** https://github.com/HULUMULU123/openclaw_assist (пустой репозиторий на момент проверки)

## Модель оркестрации

**Lead Developer → Planning → Specialized Workers → Independent Review → Integration → Verification**

### Шаги Lead Developer

1. Читает ТЗ, архитектуру и текущее состояние репозитория.
2. Разбивает задачу на атомарные подзадачи с зависимостями.
3. Назначает исполнителей по специализациям.
4. Передаёт каждому минимально необходимый контекст и контракт результата.
5. Выполняет независимые исследования параллельно.
6. Разрешает параллельную реализацию только при отсутствии конфликтующих областей записи и наличии изоляции.
7. Проверяет результаты через независимого ревьюера и автоматические тесты.
8. Интегрирует изменения и обновляет статус проекта.

## Обязательные ограничения

### Управление
- **Не более одного главного управляющего агента.** Никакого второго уровня оркестрации.
- Субагенты **не вызывают новых субагентов** без отдельного разрешения.
- Каждый исполнитель имеет **ограниченную область файлов и полномочий**.

### Изоляция параллельной работы
- Использовать **отдельные Git worktrees/ветки** при параллельных изменениях.
- **Не допускать одновременную запись в одни и те же файлы.**
- По умолчанию запускать **не более трёх независимых рабочих субагентов** одновременно; затем измерить пользу и стоимость параллелизма.

### Ревью и качество
- **Ревьюеры не подтверждают собственную реализацию.**
- Нельзя объявлять этап завершённым **без тестов и проверяемых доказательств.**
- Системные пакеты, платные API, доступ к личным данным и боевой деплой — **только в пределах разрешений исходного ТЗ.**

## Профили субагентов (команда разработки)

| Субагент | Область ответственности | Профиль (wshobson/agents) |
|---|---|---|
| `backend-architect` | Архитектура Task Core, API, границы модулей | agent-teams + c4-architecture |
| `python-pro` | Python-сервисы, асинхронность, обработка ошибок | python-development |
| `typescript-pro` | TypeScript-компоненты и SDK | javascript-typescript |
| `frontend-developer` | React-панель управления | javascript-typescript + vercel/react-best-practices |
| `database-architect` | SQLite, миграции, ограничения целостности | database-design + database-migrations |
| `ai-engineer` | LLM-интеграции, маршрутизация моделей | llm-application-dev |
| `security-auditor` | Контроль полномочий, безопасность, угрозы | security-scanning |
| `threat-modeling-expert` | Моделирование угроз и границ доверия | security-scanning |
| `test-automator` | Unit, integration, contract, E2E тесты | unit-testing |
| `code-reviewer` | Независимая проверка кода | comprehensive-review |
| `architect-reviewer` | Проверка архитектурных решений | comprehensive-review |
| `debugger` | Воспроизведение и локализация дефектов | systematic-debugging |
| `performance-engineer` | Производительность и ресурсные ограничения | observability-monitoring |
| `documentation-engineer` | Техническая документация | documentation-generation |
| `devops-troubleshooter` | Изолированные окружения, диагностика, скрипты установки | developer-essentials |

## Навыки (Skills) — минимальный обязательный набор

### P0 — база (obra/superpowers)
- `brainstorming` — архитектурный анализ и выбор решений
- `writing-plans` — декомпозиция крупных этапов
- `executing-plans` — исполнение утверждённых планов
- `subagent-driven-development` — делегирование реализации и двухэтапное ревью
- `dispatching-parallel-agents` — параллельная работа независимых субагентов
- `using-git-worktrees` — изоляция изменений
- `test-driven-development` — разработка через тестирование
- `systematic-debugging` — системная диагностика ошибок
- `requesting-code-review` — запуск независимого ревью
- `receiving-code-review` — обработка замечаний ревью
- `verification-before-completion` — проверка результата перед завершением
- `finishing-a-development-branch` — контролируемая интеграция

### P0 — безопасность (trailofbits/skills)
- `spec-to-code-compliance` — проверка реализации относительно ТЗ
- `insecure-defaults` — поиск небезопасных значений по умолчанию
- `differential-review` — анализ безопасности изменений
- `static-analysis` — интеграция статических анализаторов
- `supply-chain-risk-auditor` — аудит зависимостей
- `sharp-edges` — выявление опасных API
- `modern-python` — современные практики Python
- `property-based-testing` — тестирование инвариантов
- `regression-hunt` — поиск регрессий

### P0 — инструменты (anthropics/skills + vercel-labs)
- `mcp-builder` — создание MCP-серверов
- `skill-creator` — создание навыков
- `webapp-testing` — UI-тестирование (Playwright)
- `react-best-practices` — React-компоненты и производительность

### P1 — плагины субагентов (wshobson/agents)
- `agent-teams`, `agent-orchestration`, `developer-essentials`
- `python-development`, `javascript-typescript`
- `comprehensive-review`, `unit-testing`, `security-scanning`
- `context-management`, `database-design`, `database-migrations`
- `backend-development`, `llm-application-dev`, `full-stack-orchestration`
- `documentation-generation`, `observability-monitoring`
- `c4-architecture`, `plugin-eval`

### Референсы (VoltAgent/awesome-claude-code-subagents)
- `agent-organizer`, `task-distributor`, `workflow-orchestrator`
- `multi-agent-coordinator`, `context-manager`
- `error-coordinator`, `performance-monitor`
- **Не запускать все одновременно.** Основной контроллер — единственный.

## Антипаттерны делегирования

| AP | Описание |
|---|---|
| AP-D1 | Два ведущих агента конкурируют за управление |
| AP-D2 | Субагент запускает своих субагентов без разрешения |
| AP-D3 | Ревьюер подтверждает код, который сам написал |
| AP-D4 | Два субагента пишут в один файл одновременно |
| AP-D5 | Задача объявлена завершённой без тестов |
| AP-D6 | Markdown-файл агента принят за доказательство работающей оркестрации |

## Порядок внедрения

1. Определить coding-agent runtime (DSH в нашем случае: `subagent`/`subagent_fork`/`workflow`).
2. Проверить поддержку изолированных контекстов, параллельных задач и worktrees.
3. Скачать перечисленные репозитории, проверить лицензии, содержимое навыков, hooks, permissions.
4. Установить совместимые P0-навыки и профили специализированных исполнителей.
5. Настроить роли, маршрутизацию и ограничения.
6. Добавить собственные проектные правила из ТЗ.
7. Контрольный тест: Python-сервис + TypeScript-интерфейс + контрактные тесты.
8. Проверить независимое ревью, корректность интеграции, общий тестовый прогон.
9. Зафиксировать результат установки, версии, проблемы совместимости.

---

**Связанные документы:**
- `16-Архитектура-субагенты-навыки-интеграции-v0.2.md` — архитектура субагентов
- `15-ТЗ-поправки-v1.4.md` — поправки к ТЗ
- `context.md` — контекст проекта
- `STATUS.md` — статус этапов
- `src/skills/REGISTRY.md` — реестр вендоренных навыков