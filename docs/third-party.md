# Реестр сторонних проектов (Third-Party)

**Дата:** 11.11.2026 | **Основание:** `16` §4, S0B-T5 | **Статус:** все `claimed` до проверки

## Формат записи

| Поле | Описание |
|---|---|
| **Проект** | Имя и ссылка |
| **Роль** | Зачем нужен в нашей архитектуре |
| **Лицензия** | По LICENSE; GPL/AGPL → отдельная изоляция |
| **Последний коммит** | Дата/хеш из GitHub |
| **Телеметрия** | Есть ли отправка данных (phoning home) |
| **base_url** | Можно ли настроить прокси/шлюз (ворота G2) |
| **Ворота** | Статус G1–G7 |
| **Статус** | `claimed` / `documented-verified` / `tested_in_sim` / `tested_live` / `tested_target` / `отклонён` |
| **Примечания** | Ограничения, риски, требуемая изоляция |

---

## Каталог проектов

### 4.1. LLM-агенты (Computer Use, Desktop, Coding)

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [Agent-S](https://github.com/simular-ai/Agent-S) | Референс desktop-агента | MIT | ? | `claimed` |
| [UFO²](https://github.com/microsoft/UFO) | Референс Windows GUI-агента | MIT | ? | `claimed` |
| [OpenCode](https://github.com/opencode-ai/opencode) | Исполнитель по умолчанию в Harness² | Apache-2.0 | ? | `claimed` |
| [Codex](https://github.com/openai/codex) | Альтернативный исполнитель в Harness² | ? | ? | `claimed` |
| [browser-use](https://github.com/browser-use/browser-use) | Браузерный агент | MIT | ? | `claimed` |

### 4.1a. Браузеры и веб-доступ

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [**Obscura**](https://github.com/h4ckf0r0day/obscura) | Лёгкий read-only headless-браузер на Rust (свой движок + V8 + CDP) | **Apache-2.0** ✅ | N/A (LLM не использует) | `claimed` |

#### Детальная запись Obscura

| Поле | Значение |
|---|---|
| **Проект** | [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura) |
| **Версия** | 0.1.0 |
| **Последний коммит** | 2026-11-10 (`e300716`), автор SGavrl — активно |
| **Описание** | Независимый headless-браузер на Rust: собственный движок рендеринга (taffy + tiny-skia + ab_glyph), V8 для JavaScript, CDP-совместимый endpoint для Puppeteer/Playwright, MCP-режим |
| **Заявленные характеристики** | 30 MB RAM (vs 200+ MB Chrome), ~70 MiB бинарник, запуск «мгновенно», загрузка страницы ~85 мс, встроенный anti-detect (`--stealth`) |
| **Лицензия** | Apache-2.0 ✅ (проверено: LICENSE + Cargo.toml) |
| **Зависимости** | Rust (taffy, tiny-skia, ab_glyph, tokio, reqwest с rustls-tls, clap); V8 (через obscura-js); **без внешней телеметрии** по Cargo.toml |
| **SSRF-защита** | Встроенный crate `obscura-ssrf` |
| **Флаги безопасности** | `--stealth` (можно отключить сборкой без фичи); `--allow-private-network` (по умолчанию false); лимит ответов 2 MiB; таймаут скриптов 30 с |
| **Роль в проекте** | Лёгкий read-only уровень для research-agent (AG-04): статьи, документация, открытые источники. Экономия RAM при параллельном чтении страниц |
| **НЕ роль** | НЕ замена OpenClaw Browser/Playwright на Chromium; НЕ для входа в аккаунты/форм/изменяющих действий |
| **Ворота G1–G7** | ⏳ проверка S0B-T6 |
| **G1 (лицензия)** | ✅ Apache-2.0 |
| **G2 (base_url)** | N/A — LLM не использует |
| **G3 (sandbox)** | ⚠️ нужно проверить: CDP на 127.0.0.1, токен, очистка cookies/кэша после job |
| **G4 (закрепляемость)** | ✅ `e3007167016b169bb58d8b5124ca9662a0b37f2d` |
| **G5 (телеметрия)** | ✅ не обнаружена в Cargo.toml |
| **G6 (активность)** | ✅ коммит 10.11.2026 (<24 ч назад) |
| **G7 (классы данных)** | ⚠️ только `public`; сборка без `--stealth` обязательна |

#### Ограничения

| Ограничение | Описание |
|---|---|
| **Режим** | Только read-only: получение страниц → текст/Markdown. Без входа, паролей, MFA, сессий владельца, отправки форм |
| **Профиль** | `web-fetch-light`: только A (недоверенный ввод), без B и без C. Правило двух соблюдено |
| **Ответы** | `trust=untrusted`, `data_class=public`; извлечение полей только через AG-00 (quarantine-reader) |
| **Сборка** | Из исходников БЕЗ `--stealth`; бинарники с Releases не использовать |
| **Запуск** | Sandbox WSL, egress через прокси с allowlist доменов; CDP только на 127.0.0.1; обязателен токен из secrets broker |
| **MCP-режим** | Без approval владельца не включать; если включён — хеш описаний инструментов закреплён |
| **Лестница выбора** | Документированный API → HTTP без JS → Obscura (JS, чтение) → Playwright/Chromium → визуальный GUI |

#### ADR-N: Obscura (лёгкий read-only браузер)

| Поле | Значение |
|---|---|
| **Статус** | `claimed` |
| **Варианты** | (а) Принять как лёгкий read-only уровень; (б) принять с ограничением списка сайтов; (в) отклонить |
| **Блокирующее** | U-24 (сборка/совместимость в WSL), U-25 (совместимость с реальными источниками), В-28 (список источников) |
| **Связанные ADR** | ADR-I (Windows Companion), ADR-K/L (RAG) |

---

### 4.2. Office и документы

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [OfficeCLI](https://github.com/officecli/OfficeCLI) | CLI для Office | MIT | ? | `claimed` |
| [Office MCP](https://github.com/office-mcp/office-mcp) | MCP-сервер Office | ? | ? | `claimed` |
| [Office.js](https://github.com/OfficeDev/office-js) | JS API для Office | ? | ? | `claimed` |
| [PPT Master](https://github.com/ppt-master/PPT-Master) | Генератор презентаций | ? | ? | `claimed` |
| [SlidePoise](https://github.com/slidepoise/SlidePoise) | Генератор презентаций | ? | ? | `claimed` |
| [PPTAgent](https://github.com/ppt-agent/PPTAgent) | Агент презентаций | ? | ? | `claimed` |
| [Presenton](https://github.com/presenton/Presenton) | Генератор презентаций | ? | ? | `claimed` |
| [MinerU](https://github.com/opendatalab/MinerU) | Парсинг PDF | Apache-2.0 | ? | `claimed` |
| [Docling](https://github.com/DS4SD/docling) | Парсинг PDF | MIT | ? | `claimed` |
| [GROBID](https://github.com/kermitt2/grobid) | Извлечение библиографии | Apache-2.0 | ? | `claimed` |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | PDF-библиотека | AGPL / коммерческая | ? | `claimed` |

### 4.3. CAD и инженерное ПО

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [Autocad-MCP](https://github.com/autocad-mcp/autocad-mcp) | MCP для AutoCAD | ? | ? | `claimed` |
| [thewisekape/autocad-mcp](https://github.com/thewisekape/autocad-mcp) | Альтернативный MCP AutoCAD | ? | ? | `claimed` |
| [ezdxf](https://github.com/mozman/ezdxf) | DXF на Python | MIT | N/A | `claimed` |

### 4.4. Библиография и источники

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [Zotero CLI](https://github.com/zotero/zotero) | Управление источниками | AGPL (клиент) | N/A | `claimed` |
| [zotero-mcp](https://github.com/54yyyu/zotero-mcp) | MCP для Zotero | MIT (сервер), AGPL (плагин) | N/A | `claimed` |
| [PaperQA2](https://github.com/Future-House/PaperQA2) | Проверка цитат | Apache-2.0 | ? | `claimed` |

### 4.5. Исследования и текст

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) | Research backend | ? | ? | `claimed` |
| [Denario](https://github.com/Denario-AI/Denario) | Референс/альтернатива | **GPL-3.0** | ? | `claimed` |
| [paper-orchestra](https://github.com/google-research/paper-orchestra) | Writer/Review референс | ? | ? | `claimed` |
| [opendraft](https://github.com/federicodeponte/opendraft) | Writing backend | ? | ? | `claimed` |
| [AgentLaboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | Референс | MIT | ? | `claimed` |
| [AI-Scientist-v3](https://github.com/SakanaAI/AI-Scientist-v3) | Референс | ? | ? | `claimed` |
| [gpt-researcher](https://github.com/assafelovic/gpt-researcher) | Fallback web research | MIT | ? | `claimed` |
| [storm](https://github.com/stanford-oval/storm) | Outline/обзор | MIT | ? | `claimed` |
| [Paper2Agent](https://github.com/jmiao24/Paper2Agent) | Научный код → инструменты | ? | ? | `claimed` |

### 4.6. ГОСТ, нормоконтроль

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [gostforge](https://github.com/gostforge/gostforge) | ГОСТ-форматирование | ? | N/A | `claimed` |
| [gostdoc](https://github.com/gostdoc/gostdoc) | ГОСТ-документы | ? | N/A | `claimed` |

### 4.7. Энергетика и расчёты

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [OpenModelica](https://github.com/OpenModelica/OMPython) | Динамические модели | OSMC-PL | N/A | `claimed` |
| [pandapower](https://github.com/e2nIEE/pandapower) | Режимы сетей | BSD | N/A | `claimed` |
| [PyPSA](https://github.com/PyPSA/PyPSA) | Оптимизация энергосистем | MIT | N/A | `claimed` |
| [OpenDSSDirect.py](https://github.com/dss-extensions/OpenDSSDirect.py) | Распределительные сети | MIT | N/A | `claimed` |
| [Pint](https://github.com/hgrecco/pint) | Единицы измерения | BSD | N/A | `claimed` |
| [SciPy](https://github.com/scipy/scipy) | Расчёты | BSD | N/A | `claimed` |
| [SymPy](https://github.com/sympy/sympy) | Символьные вычисления | BSD | N/A | `claimed` |

### 4.8. RAG и эмбеддинги

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| Модель эмбеддингов (TBD, ADR-K) | Локальные эмбеддинги для RAG | TBD | N/A | `claimed` |

---

### 4.10. Рекурсивная обвязка (Harness²)

| Проект | Роль | Лицензия | G2 (base_url) | Статус |
|---|---|---|---|---|
| [**Harness²**](https://github.com/google-research/harness2) | Референс для S21 (обучение на ошибках, дельта-обновления playbook) + изолированный эксперимент S15 | **Apache-2.0** ✅ | `bridge` (litellm+fastapi) — потенциально да, через Gateway; без Vertex — неизвестно | `claimed` |

#### Детальная запись Harness²

| Поле | Значение |
|---|---|
| **Проект** | [google-research/harness2](https://github.com/google-research/harness2) |
| **Версия** | 0.1.0 |
| **Описание** | Фреймворк рекурсивной «обвязки» агента при фиксированных весах модели. Цикл Propose–Probe–Compose на уровне задачи + постоянная «improvement harness» с принятыми обвязками и уроками |
| **Редактируемые компоненты** | system prompt, guardrails, memory, tool guidance, subagents, skills, scripts, plugins (8 компонентов) |
| **Исполнители** | OpenCode (по умолчанию), Codex |
| **Лицензия** | Apache-2.0 ✅ (подтверждено: LICENSE + third_party/README) |
| **Python** | >=3.12, <3.14 (совместимо с нашим 3.13) |
| **Зависимости** | `litellm[proxy]==1.95.0`, `fastapi==0.139.2`, `google-auth==2.56.3` (bridge); `openpyxl`, `python-pptx` (render); Node.js 20+ для бенчмарков |
| **Облачная привязка** | Vertex AI + Google Cloud CLI + `GOOGLE_CLOUD_PROJECT` (требуется по умолчанию). Без Vertex — неизвестно (U-23) |
| **Песочница** | Codex sandbox **отключена по умолчанию** (README). Требуется закрыть своими средствами |
| **Сеть** | Нет ограничений (README). Требуется allowlist |
| **Стоимость** | k=1: 4 прогона исполнителя + вызовы редактора/судьи; k=5: 20 прогонов. Метрика: $/принятый результат |
| **Прирост на бенчмарках (claimed)** | GLM-5: +11.5 пт WorkBuddy, +4.5 пт JobBench, +11.8 п.п. LAB partial. **Не критерий приёмки — заявление авторов** |
| **Роль в проекте** | (а) Референс для S21 (postmortem→lessons, дельта-обновления playbook, §6B.4-H); (б) изолированный офлайн-эксперимент S15 («фиксированная vs улучшенная обвязка» на ≥10 задачах) |
| **НЕ роль** | НЕ runtime-компонент, НЕ часть Task Core, НЕ замена оркестратора |
| **Ворота G1–G7** | ⏳ проверка S0B-T6 |
| **G1 (лицензия)** | ✅ Apache-2.0 |
| **G2 (base_url)** | ⚠️ bridge на litellm — потенциально да; без Vertex — U-23 |
| **G3 (телеметрия)** | ⏳ проверить |
| **G4 (песочница)** | ❌ Codex sandbox отключена — требуется закрыть средствами адаптера |
| **G5 (зависимости)** | ⏳ проверить third_party/ лицензии |
| **G6 (активность)** | ⏳ проверить дату последнего коммита |
| **G7 (размер)** | ⏳ проверить |

#### Ограничения

| Ограничение | Описание |
|---|---|
| **Редактируемая поверхность** | Только: tool guidance, черновики навыков, промпты рабочих профилей, дельты playbook. ЗАПРЕЩЕНО: policy, guardrails, права, allowlist, бюджеты, секреты, код ядра, Gateway |
| **Результат** | Только предложения (patch + тест + трасса) в очередь ревью владельца. Прямая запись в `active` запрещена |
| **Сгенерированные скрипты/плагины** | Недоверенный код |
| **Запуск** | Только sandbox (синтетические/обезличенные данные, класс `public`), egress — allowlist, внешний лимит бюджета |
| **LLM-вызовы** | Только через LLM Gateway с эфемерным ключом. Vertex AI/Google Cloud напрямую — запрещено. Если без Vertex не работает — проект исключается (G2) |
| **Пакетный режим** | Только в непиковые часы (§6C П-10) |

#### ADR-M: Harness²

| Поле | Значение |
|---|---|
| **Статус** | `claimed` |
| **Варианты** | (а) Принять как референс для S21; (б) принять как офлайн-эксперимент S15; (в) отказаться |
| **Блокирующее** | U-23: можно ли без Vertex AI через OpenAI-совместимый Gateway; В-27: разрешение владельца на эксперимент и бюджет |
| **Связанные ADR** | ADR-I (Windows Companion), ADR-J (реестр навыков), ADR-K/L (RAG) |