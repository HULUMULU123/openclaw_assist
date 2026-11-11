# Карта покрытия навыков и субагентов OpenClaw v2

**Дата:** 11.11.2026 | **Среда:** DSH (DeepSeek Harness) | **Каталог навыков:** `~/.agents/skills/`

## 1. Superpowers (obra/superpowers) — 12/12 ✅ ПОЛНОЕ ПОКРЫТИЕ

Уже установлены в `~/.agents/skills/` (4.11.2026). Вендорены в `src/skills/`.

| Навык | ~/.agents/skills | src/skills | Назначение |
|---|---|---|---|
| `brainstorming` | ✅ | ✅ | Архитектурный анализ и выбор решений |
| `writing-plans` | ✅ | ✅ | Декомпозиция крупных этапов |
| `executing-plans` | ✅ | ✅ | Исполнение утверждённых планов |
| `subagent-driven-development` | ✅ | ✅ | Делегирование реализации и двухэтапное ревью |
| `dispatching-parallel-agents` | ✅ | ✅ | Параллельная работа независимых субагентов |
| `using-git-worktrees` | ✅ | ✅ | Изоляция изменений |
| `test-driven-development` | ✅ | ✅ | Разработка через тестирование |
| `systematic-debugging` | ✅ | ✅ | Системная диагностика ошибок |
| `requesting-code-review` | ✅ | ✅ | Запуск независимого ревью |
| `receiving-code-review` | ✅ | ✅ | Обработка замечаний ревью |
| `verification-before-completion` | ✅ | ✅ | Проверка результата перед завершением |
| `finishing-a-development-branch` | ✅ | ✅ | Контролируемая интеграция |

**Лицензия:** MIT | **Репозиторий:** https://github.com/obra/superpowers | **Версия:** shallow HEAD (4.11.2026)

---

## 2. trailofbits/skills — 9/9 ✅ ВСЕ НАЙДЕНЫ

Скачаны в `/tmp/trailofbits-skills/`. **Формат:** плагины Claude Code (`.mdc`), НЕ навыки DSH. Требуют адаптации.

| Плагин | Найден | DSH-эквивалент | Назначение |
|---|---|---|---|
| `spec-to-code-compliance` | ✅ | `spec-driven-development` | Проверка реализации относительно ТЗ |
| `insecure-defaults` | ✅ | `security-and-hardening` | Поиск небезопасных значений по умолчанию |
| `differential-review` | ✅ | `code-review-and-quality` | Анализ безопасности изменений |
| `static-analysis` | ✅ | `security-and-hardening` | Интеграция статических анализаторов |
| `supply-chain-risk-auditor` | ✅ | `security-and-hardening` | Аудит зависимостей |
| `sharp-edges` | ✅ | `security-and-hardening` | Выявление опасных API |
| `modern-python` | ✅ | — (нет прямого аналога) | Современные практики Python |
| `property-based-testing` | ✅ | `test-driven-development` | Тестирование инвариантов |
| `regression-hunt` | ✅ | `systematic-debugging` | Поиск регрессий |

**Лицензия:** CC BY-SA 4.0 ⚠️ (share-alike — требует сохранения лицензии в производных работах)  
**Репозиторий:** https://github.com/trailofbits/skills  
**Статус:** скачаны для референса. Для использования нужна адаптация из `.mdc` в DSH-навыки.

---

## 3. wshobson/agents — 18/18 ✅ ВСЕ НАЙДЕНЫ

Скачаны в `/tmp/wshobson-agents/`. **Формат:** плагины Claude Code с определениями субагентов. DSH использует собственный механизм `subagent`/`subagent_fork`.

| Плагин | Приоритет | Найден | Назначение |
|---|---|---|---|
| `agent-teams` | P0 | ✅ | Команды агентов |
| `agent-orchestration` | P0 | ✅ | Оркестрация |
| `developer-essentials` | P0 | ✅ | Базовые инструменты разработчика |
| `python-development` | P0 | ✅ | Python-разработка |
| `javascript-typescript` | P0 | ✅ | JS/TS-разработка |
| `comprehensive-review` | P0 | ✅ | Всестороннее ревью |
| `unit-testing` | P0 | ✅ | Модульное тестирование |
| `security-scanning` | P0 | ✅ | Сканирование безопасности |
| `context-management` | P0 | ✅ | Управление контекстом |
| `database-design` | P1 | ✅ | Проектирование БД |
| `database-migrations` | P1 | ✅ | Миграции БД |
| `backend-development` | P1 | ✅ | Бэкенд-разработка |
| `llm-application-dev` | P1 | ✅ | LLM-приложения |
| `full-stack-orchestration` | P1 | ✅ | Full-stack оркестрация |
| `documentation-generation` | P1 | ✅ | Генерация документации |
| `observability-monitoring` | P1 | ✅ | Наблюдаемость и мониторинг |
| `c4-architecture` | P1 | ✅ | C4-архитектурные диаграммы |
| `plugin-eval` | P1 | ✅ | Оценка плагинов |

**Лицензия:** MIT | **Репозиторий:** https://github.com/wshobson/agents  
**Статус:** скачаны для референса. Профили субагентов используются как шаблоны для DSH `subagent` prompt.

---

## 4. anthropics/skills — 3/3 ✅ ПОЛНОЕ ПОКРЫТИЕ

Уже в `~/.agents/skills/` (встроенные DSH-навыки).

| Навык | В каталоге | Назначение |
|---|---|---|
| `mcp-builder` | ✅ | Создание MCP-серверов |
| `skill-creator` | ✅ | Создание навыков |
| `webapp-testing` | ✅ | UI-тестирование (Playwright) |

**Дополнительно:** `vercel-react-best-practices` ✅ (в каталоге DSH)

---

## 5. VoltAgent/awesome-claude-code-subagents — 7/7 ✅ РЕФЕРЕНСЫ

Скачаны в `/tmp/voltagent-subagents/`. Каталог `categories/09-meta-orchestration/`.

| Референс | Назначение | Статус |
|---|---|---|
| `agent-organizer` | Организация агентов | референс |
| `task-distributor` | Распределение задач | референс |
| `workflow-orchestrator` | Оркестрация рабочих процессов | референс |
| `multi-agent-coordinator` | Координация множественных агентов | референс |
| `context-manager` | Управление контекстом | референс |
| `error-coordinator` | Координация ошибок | референс |
| `performance-monitor` | Мониторинг производительности | референс |

**Лицензия:** MIT | **Репозиторий:** https://github.com/VoltAgent/awesome-claude-code-subagents  
**Статус:** референсы. Не запускать все одновременно.

---

## 6. Команда субагентов — соответствие профилей

| Роль | wshobson-плагин | Назначение |
|---|---|---|
| `backend-architect` | `c4-architecture` + `agent-teams` | Архитектура, API, границы модулей |
| `python-pro` | `python-development` | Python-сервисы, асинхронность |
| `typescript-pro` | `javascript-typescript` | TypeScript-компоненты |
| `frontend-developer` | `javascript-typescript` + `vercel-react-best-practices` | React-панель |
| `database-architect` | `database-design` + `database-migrations` | SQLite, миграции |
| `ai-engineer` | `llm-application-dev` | LLM-интеграции |
| `security-auditor` | `security-scanning` | Безопасность |
| `threat-modeling-expert` | `security-scanning` | Моделирование угроз |
| `test-automator` | `unit-testing` | Тесты |
| `code-reviewer` | `comprehensive-review` | Ревью кода |
| `architect-reviewer` | `comprehensive-review` | Ревью архитектуры |
| `debugger` | `systematic-debugging` | Локализация дефектов |
| `performance-engineer` | `observability-monitoring` | Производительность |
| `documentation-engineer` | `documentation-generation` | Документация |
| `devops-troubleshooter` | `developer-essentials` | Окружения, диагностика |

---

## 7. Итоговая статистика

| Источник | Запрошено | Найдено | Покрытие | Статус |
|---|---|---|---|---|
| obra/superpowers | 12 | 12 | 100% | ✅ Установлены в `~/.agents/skills/` |
| trailofbits/skills | 9 | 9 | 100% | 📥 Скачаны, нужна адаптация `.mdc`→DSH |
| wshobson/agents | 18 | 18 | 100% | 📥 Скачаны, референс для профилей |
| anthropics/skills | 3 | 3 | 100% | ✅ В каталоге DSH |
| vercel-labs | 1 | 1 | 100% | ✅ `vercel-react-best-practices` |
| VoltAgent | 7 | 7 | 100% | 📥 Скачаны, референсы |
| **ВСЕГО** | **50** | **50** | **100%** | |

---

## 8. Пробелы и риски

| # | Пробел | Влияние | План |
|---|---|---|---|
| 1 | trailofbits — формат `.mdc` (Claude Code), не DSH | Нельзя загрузить через `skill()` напрямую | Адаптировать критичные (spec-to-code-compliance, insecure-defaults) в формат SKILL.md |
| 2 | trailofbits — лицензия CC BY-SA 4.0 | Share-alike: производные работы должны быть под той же лицензией | Документировать в `third-party.md` |
| 3 | wshobson/agents — формат плагинов Claude Code | DSH использует `subagent`/`subagent_fork` с произвольным prompt | Профили субагентов — референс, не установка |
| 4 | `modern-python` — нет прямого DSH-эквивалента | Python-практики trailofbits недоступны как навык | Использовать как референс при код-ревью |
| 5 | `property-based-testing` — нет в DSH | Hypothesis/инварианты не покрыты навыком | Ручное применение + `test-driven-development` |

---

## Связанные документы

- `docs/delegation-principles.md` — принципы делегирования
- `docs/third-party.md` — реестр внешних проектов
- `src/skills/REGISTRY.md` — реестр вендоренных навыков
- `context.md` — контекст проекта
- `~/.agents/skills/` — установленные навыки DSH (162 папки)
- `/tmp/trailofbits-skills/` — скачанные плагины trailofbits
- `/tmp/wshobson-agents/` — скачанные плагины wshobson
- `/tmp/voltagent-subagents/` — скачанные референсы VoltAgent