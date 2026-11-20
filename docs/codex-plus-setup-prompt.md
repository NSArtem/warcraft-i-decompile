# Промпт для настройки OpenAI / Codex Plus ($20/мес) для sol / luna / terra

Изучи этот репозиторий (`/mnt/data/projects/warcraft-1-decompile`), `AGENTS.md`, отчёт `docs/claude-pro-decompilation-strategy-by-neon.md` и уже реализованный пайплайн экономии токенов для Claude Pro:
- `tools/wc1/dossier.py`
- `tools/wc1/match.py`
- `tools/wc1/permuter.py`
- `tools/wc1/t4spec.py`
- `tools/wc1/batch_driver.py`
- `tools/wc1/overnight.py`

Задача: спроектировать, реализовать и проверить в бою аналогичный ультра-экономный автономный пайплайн (включая ночной zero-supervisor раннер `wc1.overnight`) для моей подписки **OpenAI / Codex Plus ($20/мес)** с использованием моделей **sol / luna / terra** (проверь локальный `codex --help`, `codex exec --help`, конфиги/логи в `~/.codex/`, доступные модели, уровни `reasoning_effort`, JSON/schema-вывод, работу prompt caching и фактический формат ошибок rate-limit у Codex CLI на OAuth-подписке).

Требования:
1. **Не сломать текущий Claude Pro backend** — сделать чистую поддержку `--provider claude|codex` (и опционально `--provider both` / failover при rate-limit, чтобы можно было гонять либо только Codex, либо Claude + Codex вместе).
2. **Не ограничиваться очевидным «просто переключи модель на mini»** — проанализируй реальные особенности Codex CLI и моделей `sol` / `luna` / `terra`:
   - как работает headless-режим (`codex exec`, `--output-schema`, `--json`, отключение лишних tools, сохранение prefix prompt cache между вызовами);
   - как разложить staged `model` + `reasoning_effort` по этапам (Stage 1 семантика, Stage 2 черновик C, Stage 3 T3-ремонт по `first_diff`, Stage 4 T4-тесты и patch-ретраи, изолированный ремонтник в `overnight.py`) с учётом того, что смена модели может ломать кэш;
   - как корректно вести леджер расхода токенов/кэша и поддерживать дробный `--window-budget` (`0.0..1.0`, где `1.0` = тратить окно целиком до реального rate-limit, затем спать до восстановления и продолжать) с учётом реальных 5h/weekly лимитов подписки Codex $20.
3. **Сначала план и smoke-тест:**
   - исследуй локальный `codex` CLI и при наличии прошлых сессий (`~/.codex/sessions/...`) разбери реальные цифры расхода;
   - сохрани сравнительный анализ и план в `docs/codex-plus-decompilation-strategy-by-neon.md` и покажи мне план до правок кода;
   - после моего подтверждения реализуй backend + тесты (`make verify` зелёный на каждом атомарном коммите), прогони 1–2 пилотных модуля через `wc1.batch_driver --provider codex` и проверь `wc1.overnight --provider codex --dry-run`, замерив реальную экономию токенов, cache hit rate и качество T3/T4.
4. Соблюдай все правила `AGENTS.md` (все команды через `nix develop -c`, не трогать чужой untracked WIP, не менять гейты `GOAL.md`, не ссылаться на Ghidra в `evidence`, банить `@pytest.mark.xfail`/skip-читы).
