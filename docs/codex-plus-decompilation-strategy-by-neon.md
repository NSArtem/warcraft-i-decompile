# Codex Plus ($20/мес) backend для `wc1.overnight` — исследование, архитектура и план подбора моделей OpenAI

Автор: Gemini 4 Neon, 2026-11-22 (ветка `codex-plus-v1`).
Этап 1 выполнен строго без вызовов моделей: все выводы опираются на локальный CLI `codex-cli 0.171.0`, метаданные `~/.codex/models_cache.json`, структуру `~/.codex/config.toml` (без чтения `auth.json`), агрегированную телеметрию 547 локальных сессий в `~/.codex/sessions/`, локальную проверку `codex debug prompt-input`, аудит кода `tools/wc1/{batch_driver,overnight,live,tui}.py` и публичную документацию OpenAI Structured Outputs / Codex CLI.

---

## 1. Факты о локальном Codex CLI (`codex-cli 0.171.0`) и метаданных

### 1.1 OAuth, план и headless-режим (`codex exec`)
- Установлена версия `codex-cli 0.171.0` (NixOS, `/run/current-system/sw/bin/codex`).
- Аутентификация: подписка **ChatGPT/Codex Plus** (`plan_type: "plus"` зафиксировано в `rate_limits` последней локальной сессии от `2026-11-22T09:06:41Z`, `auth.json` не читался).
- Headless-вызов: `codex exec` поддерживает:
  - `--json` — потоковый JSONL на stdout (`thread.started`, `turn.started`, `item.started`, `item.updated`, `item.completed`, `turn.completed`, `turn.failed`). В `turn.completed` приходит `usage` (`input_tokens`, `cached_input_tokens`, `output_tokens`).
  - `--output-schema <FILE>` — принудительный JSON Schema для финального `agent_message` (OpenAI Structured Outputs strict mode).
  - `-o, --output-last-message <FILE>` — запись финального ответа в файл (удобный запасной канал рядом с JSONL `item.completed`).
  - `-m, --model <MODEL>` и `-c model_reasoning_effort="<effort>"` — выбор модели и уровня размышления.
  - `--ignore-user-config` — **не загружает `~/.codex/config.toml`**, но сохраняет OAuth-авторизацию и каталог `$CODEX_HOME`. Это критично, так как в пользовательском `~/.codex/config.toml` подключены 2 MCP-сервера (`node_repl`, `firefox`), 10 плагинов и `features.memories = true`.
  - `--ignore-rules` — не загружает пользовательские/проектные `.rules`.
  - `-s read-only`, `-c approval_policy="never"`, `--skip-git-repo-check`, `-C <dir>`.
  - **Намеренный отказ от `--ephemeral`:** по проверке 14 прошлых локальных `exec`-сессий в `~/.codex/sessions/` (например, `rollout-2026-10-02T19-13-12-...`, `session_meta.source == "exec"`), без `--ephemeral` `codex exec` сохраняет файл сессии `rollout-*-<thread_id>.jsonl`, где в `event_msg` (`payload.type == "token_count"`) записаны:
    - `info.total_token_usage` / `info.last_token_usage` с **`reasoning_output_tokens`** (помимо `input_tokens`, `cached_input_tokens`, `output_tokens`), и
    - **`rate_limits.primary`** и **`rate_limits.secondary`** (`used_percent`, `window_minutes`, `resets_at`, `plan_type`, `rate_limit_reached_type`).
    *Статус проверки:* наличие `rate_limits` в `rollout-*-<thread_id>.jsonl` подтверждено на исторической `exec`-сессии; точное поведение в `codex-cli 0.171.0` под `--ignore-user-config` будет подтверждено на первом боевом вызове этапа 3 (в коде предусмотрен безопасный фолбэк, если `rate_limits` не окажется ни в stdout JSONL, ни в файле сессии).

### 1.2 Автоподгрузка `AGENTS.md`, MCP, инструментов и стабильный кэшируемый префикс
Проверено локально без вызовов моделей через `codex debug prompt-input`:
- **По умолчанию** (без флагов отключения) Codex собирает ~88.5k символов служебного контекста: 28.5k описания инструментов + MCP, 28.4k встроенных инструкций, 12.3k developer-инструкций, 16.0k пользовательского контекста с **автоматически подгруженным `AGENTS.md`**.
- **С флагами изоляции** (`--ignore-user-config`, `--ignore-rules`, `-s read-only`, `-c approval_policy="never"`, `-c project_doc_max_bytes=0`, `-c include_environment_context=false`, `-c model_instructions_file="<abs_sys_prompt>"`, `-c web_search="disabled"`, `-c features.shell_tool=false`, `-c features.unified_exec=false`, `-c features.plugins=false`, `-c features.apps=false`, `-c features.memories=false`, `-c features.multi_agent=false`, `-c features.view_image=false`, `-c features.hooks=false`, `-c features.skill_search=false`, `-c features.goals=false`, `-c features.sleep_tool=false`, `-c features.computer_use=false`, `-c features.browser_use=false`, `-c features.image_generation=false`, `-c features.tool_suggest=false`):
  - `AGENTS.md` полностью исключён (`project_doc_max_bytes=0`: 15,983 → 0 символов).
  - Динамический `<environment_context>` (cwd/дата/таймзона) полностью исключён (`include_environment_context=false`), что убирает разрыв кэша префикса между вызовами.
  - Встроенный 28.4k system prompt заменён на наш стабильный файл `-c model_instructions_file="<abs_path>"` (аналог `--system-prompt-file` у Claude), куда кладётся `DEFAULT_RULES` + эталоны 10.0a + `src/include/war.h` + явный запрет на вызов любых инструментов.
  - **Наблюдаемое ограничение `codex-cli 0.171.0`:** даже при отключённых `features.*` и пустом `CODEX_HOME`, локальный `codex debug prompt-input` всё равно добавляет ~34k символов встроенного декларативного слоя (`additional_tools`: группы `functions`/`collaboration`, плюс шаблон `<skills_instructions>` / `<multi_agent_role>`). Поэтому для гарантии, что модель на Stage 1–4 ничего не прочитает и не изменит в checkout:
    1. `-C <repo>/build/driver/codex_empty_cwd` — выделенная **постоянная пустая директория** (не checkout и не случайный `/tmp/...`), плюс `--skip-git-repo-check` и `-s read-only`;
    2. явный запрет в `model_instructions_file` вызывать инструменты;
    3. контроль потока `--json` в драйвере: появление `command_execution` / `file_change` / `mcp_tool_call` фиксируется как нарушение и отклоняется.
- **Про кэш префикса:** наличие и процент попадания prompt-кэша на реальных headless-вызовах `codex exec` пока **не подтверждены** (будут измерены в этапе 3 по полю `cached_input_tokens / input_tokens`). В исторических интерактивных сессиях `~/.codex/sessions/` кэш активно работает (до 90–96% `cached_input_tokens`).

### 1.3 Аудит 5 JSON-схем `batch_driver.py` на совместимость со strict-режимом OpenAI
OpenAI Structured Outputs (`strict: true`, используемый `codex exec --output-schema`) требует:
1. `"additionalProperties": false` на **каждом** объекте в схеме;
2. **каждый** ключ из `properties` обязан быть перечислен в `required`;
3. запрещены ключевые слова валидации длины/размера массивов вроде `minItems` / `maxItems`.

Несовместимости в текущих 5 схемах `tools/wc1/batch_driver.py`:
| Схема | Проблемы со strict-режимом OpenAI | Решение в V1 |
|---|---|---|
| `SEMANTIC_SCHEMA` | Нет `additionalProperties: false` на корне, `data_symbols.items`, `functions.items`; `minItems: 1` у `evidence` | Конвертер `_codex_strict_schema()` рекурсивно добавляет `additionalProperties: false`, включает все `properties` в `required` и удаляет `minItems` (непустота `evidence` уже гарантируется в Python `_sanitize_evidence`) |
| `BATCH_C_SCHEMA` | Нет `additionalProperties: false` на корне и `files.items`; опциональное поле `header_additions` не в `required` | Добавить `header_additions` в `required` (пустая строка `""` уже означает «без добавлений», совместимо с `if res.get("header_additions"):`) |
| `REPAIR_C_SCHEMA` | Нет `additionalProperties: false` на корне и `fixes.items` | Автоматически добавляется `_codex_strict_schema()` |
| `T4_AND_DOC_SCHEMA` | Нет `additionalProperties: false` на корне и `ref_verified_by.items` | Автоматически добавляется `_codex_strict_schema()` |
| `T4_PATCH_SCHEMA` | Нет `additionalProperties: false` на корне, `diagnosis`, `ref_patches.items`, `test_patches.items` | Автоматически добавляется `_codex_strict_schema()` |

Конвертация через `_codex_strict_schema(schema)` применяется на пути Codex, не меняя схемы Claude и не рискуя регрессиями Claude.

---

## 2. Доступные модели OpenAI и эмпирическая оценка «цены» в квоте (guesstimation)

### 2.1 Точные ID моделей из `~/.codex/models_cache.json` (`visibility = "list"`)
| ID модели | Display name | Контекст | Доступные `reasoning_effort` | Статус для бенчмарка |
|---|---|---:|---|---|
| `gpt-6-luna` | GPT-6-Luna | 272k | `low`, `medium`, `high`, `xhigh`, `max` (def `medium`) | **Кандидат #1** (самая лёгкая/дешёвая актуальная) |
| `gpt-5.6-luna` | GPT-5.6-Luna | 272k | `low`, `medium`, `high`, `xhigh`, `max` (def `medium`) | Резерв (legacy luna) |
| `gpt-6.1-terra` | GPT-6.1 Terra | 500k | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` (def `low`) | **Кандидат #2** (средний эффективный тир; нет локальной истории квот — непроверено) |
| `gpt-6.2-sol` | GPT-6.2-Sol | 500k | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` (def `low`) | **Кандидат #3** (актуальная основная coding-модель) |
| `gpt-6.1-sol` | GPT-6.1-Sol | 500k | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` (def `low`) | Резерв (предыдущее поколение sol) |
| `gpt-6-sol` / `gpt-5.6-sol` / `gpt-5.6-terra` | Legacy | 272k | `low..max/ultra` | Вне приоритета (legacy) |
| `gpt-6.2-astra`, `gpt-6-astra` | Astra | 272k | `low..ultra` | **ИСКЛЮЧЕНЫ** (сверхдорогие модели) |

Уровни размышления `xhigh`, `max`, `ultra` **исключены** из тестов и дефолтов. Целевые уровни: `low` и `medium` (`high` проверяется точечно на Stage 1/3 только если `medium` явно не тянет).

### 2.2 Эмпирическая оценка расхода квоты по `~/.codex/sessions/` (**GUESSTIMATION**, не гарантия)
Из 547 локальных сессий отобраны последовательные `token_count`-события в пределах одного окна (`resets_at` совпадает) с положительным шагом `used_percent`. Для нормализации введена условная метрика взвешенных единиц `WU = fresh_in + 0.1 * cached_in + 4 * out` (приближение; реальная формула биллинга OpenAI закрыта и может меняться):

| Модель (исторические сессии) | Ходов `n` | Fresh in | Cached in | Output (reas) | Σ Δ`primary` (5h) | Оценка `pp / ход` | Оценка `pp / 1M WU` | Отношение `Δ7d / Δ5h` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `gpt-6-luna` | 148 | 1.08M | 12.57M | 0.07M (0.05M) | 12.0 п.п. | **~0.081 п.п.** | **~4.6 п.п.** | ~0.25 (малая выборка) |
| `gpt-5.6-luna` | 804 | 3.25M | 73.97M | 0.48M (0.25M) | 62.0 п.п. | **~0.077 п.п.** | **~4.9 п.п.** | ~0.081 |
| `gpt-6.2-sol` | 83 | 0.22M | 4.60M | 0.04M (0.01M) | 17.0 п.п. | **~0.205 п.п.** | **~20.5 п.п.** | ~0.118 |
| `gpt-6.1-sol` | 2350 | 7.24M | 220.09M | 1.13M (0.26M) | 789.0 п.п. | ~0.336 п.п. | ~23.4 п.п. | ~0.177 |
| `gpt-5.6-terra` | 204 | 0.81M | 17.24M | 0.16M (0.04M) | 69.0 п.п. | ~0.338 п.п. | ~21.8 п.п. | ~0.174 |
| `gpt-6-astra` *(справочно, исключена)* | 13 | 0.09M | 0.83M | 0.002M | 12.0 п.п. | ~0.923 п.п. | ~66.2 п.п. | ~0.083 |
| `gpt-6.1-terra` | 0 | — | — | — | — | *непроверено* | *непроверено* | *непроверено* |

**Ключевой вывод из guesstimation:**
- `luna` обходится примерно в **4–5× дешевле** по квоте на единицу работы, чем `sol`, и в **~14× дешевле**, чем `astra`.
- Типичный 5–6-вызовный чанк (~25k fresh + ~120k cached + ~12k output ≈ 85k WU) по этой грубой оценке потратит:
  - на `gpt-6-luna`: ~0.4–1.0 п.п. `primary` (5h) и ~0.1–0.2 п.п. `secondary` (7d);
  - на `gpt-6.2-sol`: ~1.8–4.0 п.п. `primary` (5h) и ~0.3–0.7 п.п. `secondary` (7d).
- Все значения выше — **историческая оценка по интерактивным сессиям**; в этапе 3 приоритет всегда за наблюдаемым `used_percent`, а оценка используется только как запасной ограничитель при отсутствии живой телеметрии.

---

## 3. Архитектура V1 (`--provider codex`) и семантика флагов

### 3.1 CLI, изоляция провайдеров и матрица `(model, effort)` по стадиям
- В `wc1.batch_driver` и `wc1.overnight` добавляется `--provider claude|codex` (дефолт `claude` — поведение Claude не меняется).
- Настраиваемая матрица `(model, effort)` по 5 стадиям для Codex:
  - `stage1` (семантика, `SEMANTIC_SCHEMA`)
  - `stage2` (черновик C, `BATCH_C_SCHEMA`)
  - `stage3` (T3-ремонт по `first_diff`, `REPAIR_C_SCHEMA`)
  - `stage4` (T4-тесты + doc + patch-ретраи, `T4_AND_DOC_SCHEMA` / `T4_PATCH_SCHEMA`)
  - `repair` (структурированный патч-ремонт после `make verify`)
  - Флаги CLI: `--codex-model` (единая модель по умолчанию для всех стадий), `--codex-effort` (единый effort по умолчанию), плюс постадийные переопределения `--codex-stage1`, `--codex-stage2`, `--codex-stage3`, `--codex-stage4`, `--codex-repair` в формате `MODEL[:EFFORT]` (валидируя запрет `astra` и `xhigh`/`max`/`ultra` в дефолтах; при необходимости allow-list усилий `low|medium|high`).
- **Раздельный учёт и леджеры:**
  - Записи Codex пишутся в леджер со стадией `codex_call` (и `provider: "codex"`), с явным разделением:
    - наблюдаемых полей: `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`, `rate_limits_before`, `rate_limits_after`, `primary_delta_pp`, `secondary_delta_pp`;
    - оценочных полей (если живых `rate_limits` нет): `estimated: true`, `estimated_primary_pp`.
  - Старые леджеры Claude (`stage == "claude_call"`) полностью совместимы; `ledger_metrics()` и `rolling_window_spend()` фильтруют по провайдеру и никогда не смешивают Codex-токены с Claude USD.
  - Файл квот Codex отделён от Claude: `build/live/rate_limits_codex.json` (Claude остаётся на `build/live/rate_limits.json`).

### 3.2 Семантика USD-флагов под `--provider codex`
| Флаг | Поведение при `--provider claude` | Поведение при `--provider codex` |
|---|---|---|
| `--module-budget` (USD) | Жёсткий порог USD на чанк | **Не применяется** (Codex не переводит токены в USD; чанк ограничен `--module-calls`, `--max-t3-retries` и механическим per-call контролем квоты). При явной передаче печатается предупреждение/пометка, что для Codex действует `--module-calls`. |
| `--repair-budget` (USD) | Бюджет USD на `claude -p` ремонт | **Не применяется** для Codex; число раундов структурированного патч-ремонта после `make verify` задаётся `--codex-repair-calls` (в V1 по умолчанию `0` или `1` — только безопасный структурированный патч с проверкой allowlist + anti-weakening + cheat prefilter **до записи**; при `0` пост-verify ремонт отключён). |
| `--window-capacity` (USD) | Оценка ёмкости 5h окна Claude в USD | **Не применяется** для Codex (квота Codex измеряется напрямую в `%` окон `primary`/`secondary`, без перевода в USD). |

### 3.3 Критерий свежести телеметрии, холодный старт и обработка квот
- **Источники телеметрии Codex:**
  1. Прямые события из `codex exec --json` (если CLI их отдаёт) или rollout-файл `~/.codex/sessions/.../rollout-*-<thread_id>.jsonl` сразу после завершения вызова; сохраняется в `build/live/rate_limits_codex.json`.
  2. Самая свежая запись `token_count.rate_limits` в `~/.codex/sessions/**/*.jsonl` (сканируются только последние изменённые файлы, с учётом `CODEX_HOME`).
- **Критерий свежести короткого окна (`primary`):** снимок считается **свежим и подтверждённым** только если выполнены **все** условия:
  1. `primary.used_percent` — число в `[0, 100]`;
  2. `primary.resets_at` присутствует и `primary.resets_at > now` (окно ещё не сбросилось);
  3. `observed_at` (timestamp события или записи) не старше `CODEX_TELEMETRY_MAX_AGE_S` (**1800 с / 30 мин** по умолчанию, не из будущего с допуском 60 с).
- **Поведение на холодном старте при `--window-budget` в `(0.0, 1.0]`:**
  - Если `--window-budget < 1.0` (включая дефолт `0.8`): требуется **свежая подтверждённая** утилизация `primary`. Если её нет (холодный старт со старыми/отсутствующими сессиями или истёкшим `resets_at`), драйвер/раннер **не делает скрытых пробных вызовов** и **не переходит на USD-оценку**, а завершается с понятной диагностикой и ненулевым кодом возврата.
  - Если `--window-budget == 1.0`: упреждающего порога по короткому окну нет; холодный старт разрешён. Если в свежей телеметрии уже `primary.used_percent >= 100` или `secondary.used_percent >= 100` или `rate_limit_reached_type != null`, либо CLI вернул подтверждённый `rate_limit` — раннер ждёт до `resets_at + 60s` (учитывая и `primary`, и `secondary`), соблюдая `--no-sleep`.
  - **Неизвестный `resets_at`:** при подтверждённом `rate_limit`, если ни в телеметрии, ни в тексте ошибки нет будущего времени сброса — **остановка с диагностикой** (никаких бесконечных ретраев).
  - **Классификация ошибок:** обычные ошибки CLI, авторизации, сети, схемы, невалидного JSON или таймаута **не классифицируются** как `RateLimitError` (строгие маркеры: `usage_limit_reached`, `usage_limit_exceeded`, `rate_limit_exceeded`, `too many requests`, `429`, явный `rate_limit_reached_type`).
- **Механический per-call контроль квоты (внутри `batch_driver` и `overnight` перед каждым вызовом, включая ремонт):**
  - `--codex-max-5h-pct` (по умолчанию `window_budget * 100` при `<1.0`, или `100` при `1.0`);
  - `--codex-max-7d-pct` (по умолчанию `90.0` — жёсткий потолок суммарной 7d утилизации);
  - `--codex-max-7d-delta-pp` (например `25.0` на этапе 3 относительно зафиксированного `7d_start_pct`);
  - `--codex-max-total-calls` (аварийный лимит суммарных вызовов, если живой `used_percent` недоступен).

### 3.4 Безопасный структурированный ремонт после `make verify` (Codex)
На Stage 1–4 Codex никогда не имеет доступа к checkout (cwd = пустая `build/driver/codex_empty_cwd`, `-s read-only`).
Для пост-verify ремонта Codex предусмотрен только **структурированный патч** (`CODEX_VERIFY_PATCH_SCHEMA`: `diagnosis` + `file_patches: [{path, old, new}]`), который **до применения к диску** проверяется раннером:
1. Каждый `path` нормализуется и сверяется со строгим allowlist (`_check_allowed_paths`, запрещены `Makefile`, `tools/`, `war.h`, `codegen_promo.toml`, существующие tracked-тесты, чужие модули и `ref_verified_by` в TOML);
2. Любой патч к `tests/*.py` проходит in-memory проверку `find_forbidden_test_cheat()` и `check_test_patch_not_weakening(..., allow_case_edits=False)`;
3. Любой патч к `src/*.c` проходит `match.compile_check` под обоими компиляторами с автоматическим откатом при ошибке;
4. Никаких shell-команд и никаких прямых записей модель не выполняет. Флаг `--codex-repair-calls` (дефолт `1`, `0` отключает) ограничивает число таких патч-раундов.

---

## 4. Методика боевого A/B-бенчмарка (Этап 3)

### 4.1 Выбор эталонного и контрольного чанков
Из текущей очереди `wc1.overnight --dry-run` (`wave3`, чистые `full`-чанки без прежних заголовков и под стандартные флаги `-s -ot -ol -4r -zp2`):

1. **Эталонный смешанный `full`-чанк (Ступени A и B): `mod_25ba0`**
   - **6 функций, 273 инструкции** (`0x25ba0`: 57, `0x25cd8`: 46, `0x25d60`: 11, `0x25d7c`: 11, `0x25d98`: 55, `0x25e58`: 93).
   - Состав: 2 мелкие (`<=30`: 11, 11 инстр.), 1 средняя (`60–120`: 93 инстр.) и 3 промежуточных (`46, 55, 57` инстр.); 7 безымянных data-адресов; понятные соседи (`SelectionFirst`, `SelectionNext`, `StatusPanelSetUnit`, `PlaceBoxActive`, `PlaceBoxCancel`).
2. **Контрольный невиданный `full`-чанк (Ступень C): `mod_1e380` (chunk 1)**
   - **8 функций, 385 инструкций** (`0x1e380`: 20, `0x1e3b4`: 16, `0x1e3e0`: 48, `0x1e464`: 92, `0x1e584`: 67, `0x1e644`: 80, `0x1e724`: 53, `0x1e798`: 9).
   - Состав: 3 мелкие (`<=30`), 3 средние (`60–120`), 2 промежуточных (`48, 53`); 4 безымянных data-адреса.

### 4.2 Бюджет и изоляция бенчмарка
- **Короткое окно (5h / `primary`):** до ~95–100% или первого `rate_limit`.
- **Длинное окно (7d / `secondary`):** жёсткий потолок прироста **+25 п.п.** от старта (и суммарно `<= 90%`).
- **На одного кандидата:** `--module-calls 8` (и `--codex-repair-calls 1`).
- **Изоляция:** все прогоны этапа 3 идут на временной ветке `codex-plus-pilot`, сбрасываемой в чистый проверенный коммит `codex-plus-v1` перед каждым кандидатом; запуск через `wc1.overnight --provider codex --headless --max-modules 1 --no-sleep --window-budget 1.0`. Никаких параллельных вызовов с того же аккаунта. Коммиты декомпиляции с `codex-plus-pilot` в `codex-plus-v1` не переносятся.

### 4.3 Трёхступенчатый план подбора и замеры кэша
1. **Ступень A — диагональный скрининг снизу вверх с Early Stopping (на `mod_25ba0`):**
   Порядок кандидатов (однородный профиль на все стадии, от самого дешёвого к более сильному; без `astra` и `xhigh`/`max`/`ultra`):
   - `A1`: `gpt-6-luna / low`
   - `A2`: `gpt-6-luna / medium`
   - `A3`: `gpt-6.1-terra / low` *(проверка неизвестного по истории тира)*
   - `A4`: `gpt-6.2-sol / low` *(и `A5`: `gpt-6.2-sol / medium`, если `low` не проходит чисто)*
   - **Early Stopping:** если кандидат провалил Stage 1 (битая схема/TOML) или Stage 2 (некомпилируемый C) — прерываем прогон сразу, не тратя квоту на Stage 3–4.
2. **Ступень B — постадийный Coordinate Descent на замороженных входах + учёт штрафа кэша:**
   - На 1–2 лидерах ступени A замораживаем выходы Stage 1 / Stage 3 и точечно (по 1 вызову, с проверкой через `wc1.match + wc1.permuter` / `pytest`) проверяем удешевление Stage 2 и Stage 4:
     - сначала понижение `effort` (`medium → low`) внутри той же модели (сохраняем тёплый префикс);
     - затем (если экономия потенциально перекрывает cold-cache miss) смену модели на более лёгкую (`sol/terra → luna`) с прямым замером `cached_input_tokens` до и после смены модели.
   - `high` на Stage 1/3 проверяется точечно только если `medium` не даёт чистого прохождения.
   - Найденные в боевых прогонах баги промптов / strict-схем / кэша префикса фиксируются атомарными коммитами на `codex-plus-v1` (с зелёным `make verify`).
3. **Ступень C — Парето-выбор и контрольный прогон:**
   - Из профилей на Парето-фронте с чистым `make verify` и валидными T3/T4 выбирается минимум `Δ5h п.п. / принятая функция` (и `Δ7d п.п. / принятая функция`).
   - Победитель прогоняется один раз на контрольном чанке `mod_1e380` (8 fn, 385 insns) сразу после прогрева, чтобы исключить переобучение и измерить реальный `% cached input` на холодном (вызов 1), тёплом внутри модуля (вызовы 2..N) и межмодульном префиксе.

---

## 5. Результаты боевого A/B-бенчмарка (заполняется по итогам Этапа 3)

*(Раздел будет дополнен после реализации V1 и прогона Ступеней A, B, C с итоговой сводной таблицей, сравнением с Claude и ограничениями перед ночным прогоном.)*
