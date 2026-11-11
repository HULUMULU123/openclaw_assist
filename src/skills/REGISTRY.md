# Реестр навыков агента-разработчика OpenClaw

**Дата:** 10.11.2026. **Источник:** [15-Навыки-агента-разработчика.md](../../../Релейная%20защита/15-Навыки-агента-разработчика.md)

## Легенда

- **Файл** — физически присутствует в `src/skills/<name>/SKILL.md`
- **DSH** — встроен в текущую сессию DeepSeek Harness как `available_skill`
- **P0** — ядро разработки, **P1** — профильная интеграция, **P2** — опциональный

## A. Методология разработки и контроль качества (obra/superpowers)

| Приоритет | Навык | Файл | DSH | Назначение |
|---|---|---|---|---|
| P0 | brainstorming | ✓ | ✓ | Архитектурные решения, альтернативы, ограничения HP/WSL2 |
| P0 | writing-plans | ✓ | ✓ | План этапов с файлами, зависимостями, тестами |
| P0 | executing-plans | ✓ | ✓ | Реализация по плану, фиксация состояния |
| P0 | subagent-driven-development | ✓ | ✓ | Изоляция задач, проверка по спецификации |
| P1 | dispatching-parallel-agents | ✓ | ✓ | Параллельные независимые работы |
| P0 | test-driven-development | ✓ | ✓ | Red-green-refactor |
| P0 | systematic-debugging | ✓ | ✓ | Разделение сбоев по слоям |
| P0 | verification-before-completion | ✓ | ✓ | Фактический файл/запись/тест перед «готово» |
| P0 | requesting-code-review | ✓ | ✓ | Обязательное ревью критичных изменений |
| P1 | receiving-code-review | ✓ | ✓ | Проверка замечаний, не слепое выполнение |
| P1 | using-git-worktrees | ✓ | — | Изоляция задач через git worktree |
| P1 | finishing-a-development-branch | ✓ | — | Завершение ветки, PR, cleanup |

## B. Работа с документами и дизайном (Anthropic skills)

| Приоритет | Навык | Файл | DSH | Назначение |
|---|---|---|---|---|
| P1 | brand-guidelines | ✓ | — | Палитры, брендинг |
| P1 | canvas-design | — | ✓ | Визуальные композиции |
| P1 | doc-coauthoring | ✓ | — | Написание/редактирование документов |
| P1 | pdf | — | ✓ | Чтение/верификация PDF |
| P1 | docx | — | ✓ | Word-документы |
| P1 | xlsx | — | ✓ | Excel/расчёты |
| P1 | pptx | — | ✓ | Презентации |
| P1 | frontend-design | ✓ | ✓ | Дизайн UI |

## C. Веб-панель, браузер, UI/UX (Vercel agent-skills)

| Приоритет | Навык | Файл | DSH | Назначение |
|---|---|---|---|---|
| P0 | vercel-react-best-practices | — | ✓ | Производительность React/Next.js |
| P0 | web-design-guidelines | — | ✓ | Контраст, читаемость, доступность |
| P1 | vercel-composition-patterns | — | ✓ | Компоненты задач, артефактов |
| P2 | vercel-react-view-transitions | — | ✓ | Переходы |
| P1 | writing-guidelines | ✓ | — | Текст интерфейса |

## D. Инструменты разработки (SDK/CLI)

| Приоритет | Инструмент | Статус | Назначение |
|---|---|---|---|
| P0 | Playwright | ✓ MCP | E2E-тестирование |
| P0 | Context7 | ✓ MCP | Документация библиотек |
| P0 | Agent Skills Spec | agentskills.io | Переносимый формат навыков |

## E. Специализированные навыки (custom — предстоит написать)

| Приоритет | Навык | Назначение |
|---|---|---|
| P0 | model-routing-evals | Сравнительные прогоны моделей |
| P0 | wsl-windows-interop | Взаимодействие WSL↔Windows |
| P0 | artifact-verification | Проверка артефактов |
| P0 | resource-budgeting | Бюджетирование ресурсов |
| P0 | prompt-injection-tests | Тесты на инъекции |
| P0 | restore-rehearsal | Тренировка восстановления |

## F. Безопасность и контроль качества (trailofbits/skills)

**⚠️ Формат:** плагины Claude Code (`.mdc`), НЕ навыки DSH. Требуют адаптации. Лицензия: CC BY-SA 4.0. Скачаны 11.11.2026.

| Приоритет | Плагин | Назначение | DSH-эквивалент |
|---|---|---|---|
| P0 | spec-to-code-compliance | Проверка реализации относительно ТЗ | `spec-driven-development` |
| P0 | insecure-defaults | Поиск небезопасных значений по умолчанию | `security-and-hardening` |
| P0 | differential-review | Анализ безопасности изменений | `code-review-and-quality` |
| P1 | static-analysis | Интеграция статических анализаторов | `security-and-hardening` |
| P1 | supply-chain-risk-auditor | Аудит зависимостей | `security-and-hardening` |
| P1 | sharp-edges | Выявление опасных API | `security-and-hardening` |
| P1 | modern-python | Современные практики Python | — (референс) |
| P1 | property-based-testing | Тестирование инвариантов | `test-driven-development` |
| P1 | regression-hunt | Поиск регрессий | `systematic-debugging` |

## G. Профили субагентов (wshobson/agents)

**⚠️ Формат:** плагины Claude Code. DSH использует встроенный `subagent`/`subagent_fork`.  
Лицензия: MIT. Скачаны 11.11.2026.

| Приоритет | Плагин | Роль в команде |
|---|---|---|
| P0 | agent-teams | Команды агентов |
| P0 | agent-orchestration | Оркестрация |
| P0 | developer-essentials | devops-troubleshooter |
| P0 | python-development | python-pro |
| P0 | javascript-typescript | typescript-pro, frontend-developer |
| P0 | comprehensive-review | code-reviewer, architect-reviewer |
| P0 | unit-testing | test-automator |
| P0 | security-scanning | security-auditor, threat-modeling-expert |
| P0 | context-management | Управление контекстом |
| P1 | database-design | database-architect |
| P1 | database-migrations | database-architect |
| P1 | backend-development | backend-architect |
| P1 | llm-application-dev | ai-engineer |
| P1 | full-stack-orchestration | Интеграция |
| P1 | documentation-generation | documentation-engineer |
| P1 | observability-monitoring | performance-engineer |
| P1 | c4-architecture | backend-architect |
| P1 | plugin-eval | Оценка плагинов |

## H. Референсы оркестрации (VoltAgent/awesome-claude-code-subagents)

Лицензия: MIT. Скачаны 11.11.2026. Каталог `categories/09-meta-orchestration/`.

| Референс | Назначение | Статус |
|---|---|---|
| agent-organizer | Организация агентов | референс |
| task-distributor | Распределение задач | референс |
| workflow-orchestrator | Оркестрация процессов | референс |
| multi-agent-coordinator | Координация агентов | референс |
| context-manager | Управление контекстом | референс |
| error-coordinator | Координация ошибок | референс |
| performance-monitor | Мониторинг | референс |

## Версии и происхождение

| Репозиторий | Commit | Лицензия | Дата клонирования |
|---|---|---|---|
| obra/superpowers | shallow HEAD | MIT | 10.11.2026 |
| anthropics/skills | shallow HEAD | Apache-2.0 | 10.11.2026 |
| vercel-labs/agent-skills | shallow HEAD | — | 10.11.2026 |
| trailofbits/skills | shallow HEAD | CC BY-SA 4.0 | 11.11.2026 |
| wshobson/agents | shallow HEAD | MIT | 11.11.2026 |
| VoltAgent/awesome-claude-code-subagents | shallow HEAD | MIT | 11.11.2026 |