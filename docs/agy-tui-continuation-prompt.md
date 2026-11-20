# Задача для продолжения разработки `wc1.tui`

Продолжи и полностью заверши разработку красивого интерактивного TUI в стиле
`btop` для `wc1.overnight` в репозитории
`/mnt/data/projects/warcraft-1-decompile`.

Это продолжение разговора `0f8b24b2-0321-4d78-a025-39095c197779`. Требования
уже согласованы пользователем: не останавливайся на новом плане и не задавай
повторно вопросы, ответы на которые перечислены ниже. Сначала прочитай
`AGENTS.md`, `README.md`, `docs/GOAL.md`, `docs/METHODOLOGY.md` и
`docs/ANALYST_GUIDE.md`, затем проверь текущие `HEAD`, `git status`, процессы
`wc1.overnight`/`wc1.batch_driver` и сохрани всю чужую или пользовательскую WIP.

## Текущий раннер

В момент постановки задачи был запущен
`python3 -m wc1.overnight --window-budget 1.0`. Пользователь явно разрешает
**gracefully завершить текущий раннер**, если он всё ещё работает и мешает
изменять общие файлы. Не обрывай активный модуль и не теряй его работу:
дождись завершения текущего `batch_driver`, `make verify` и атомарного коммита,
останови родительский overnight-runner на границе модулей, затем проверь, что
не осталось его дочерних процессов. Если раннер уже завершился, просто
продолжай. Не откатывай и не включай в свои коммиты существующую WIP
`BULLET.C` или WIP другого модуля.

## Согласованный продукт

Используй **Textual + Rich**. `flake.nix` уже мог получить эту зависимость в
коммите `256a174`; проверь фактическое состояние, не повторяй сделанное.

Архитектура:

1. `wc1.overnight` остаётся независимым backend-runner и атомарно публикует
   live-состояние в `build/live/` (`state.json`, `rate_limits.json`,
   `workers/<id>.jsonl`, control IPC). Частично записанные файлы не должны
   ломать reader: используй atomic replace и терпимый parser/tailer.
2. `wc1.tui` — отдельный attach/detach-клиент. Он подключается к уже
   запущенному runner, переживает его перезапуск и не завершает runner при
   закрытии TUI. `q` только отсоединяет интерфейс.
3. Обычный интерактивный запуск `python3 -m wc1.overnight` открывает launcher
   через `wc1.tui`: разумные пресеты плюс редактируемые флаги. Должны остаться
   прямой запуск dashboard (`--tui`) и явный чистый backend (`--headless`);
   `--dry-run` и неинтерактивная среда не должны неожиданно открывать TUI.
4. Runner, IPC и UI не должны зависеть от долгоживущего LLM-supervisor.

Панели dashboard:

- Верхняя строка: общий прогресс `DONE/1010`, прирост текущего run, состояние
  build/verify, часы и состояние runner.
- **Quota & Pace**: реальные 5h и 7d лимиты Claude, время их сброса и порог
  `--window-budget`; fallback на rolling ledger, если live quota ещё не
  пришла; burn-rate/sparkline, cache-hit, стоимость на функцию и оценка числа
  функций до лимита. Состояния минимум: RUNNING, THINKING, PERMUTING,
  VERIFYING, REPAIRING, COMMITTING, SLEEPING, PAUSED, STOPPING, FAILED, DONE.
- **Heatmap**, переключаемый функции/модули. В режиме функций показывай все
  функции в адресном порядке; в режиме модулей — агрегаты. Легенда должна быть
  читаема не только цветом:
  - `░` тёмно-серый — untouched (нет имени и C);
  - `▒` синий — named, но C ещё нет;
  - `▓` жёлто-оранжевый — reference C без подтверждённого T4;
  - `■` бирюзовый — T4 verified;
  - `█` ярко-зелёный — T3 match;
  - `◆` magenta — сейчас в работе;
  - `✕` красный — failed/rollback в текущем run;
  - опционально `·` тусклый — out-of-scope.
  Курсор/мышь показывают inspector с адресом, именем, модулем, tier и source.
- **Agents & Queue**: активные worker/stage, завершённые элементы текущего run
  (`+N DONE`, cost, commit), failures и ближайшая очередь. Реализация должна
  позволять несколько worker и будущий provider `codex`, даже если сейчас
  runner последовательный.
- **Live Stream** выбранного worker: настоящий auto-updating thinking/text и
  локальные события TOOL/PERM/MATCH/VERIFY/COMMIT/ERROR. Стрелки/мышь выбирают
  worker; `a`/`t`/`v` фильтруют all/thinking/verification; `f`/End включает
  follow, ручная прокрутка отключает follow.

Управление:

- pause/resume — только на безопасной границе модуля;
- wake — досрочно разбудить ожидание окна;
- graceful stop — закончить текущий модуль, выполнить verify, commit либо
  штатный archive/rollback и выйти;
- immediate kill — только после подтверждения: остановить активных детей,
  архивировать/откатить только изменения текущего модуля, сохранить
  pre-existing WIP;
- просмотр последних коммитов текущего run;
- detach не должен воздействовать на runner.

## Live streaming и лимиты

Переведи вызов `claude -p` в `wc1.batch_driver` на
`--output-format stream-json --verbose --include-partial-messages`, сохранив
structured JSON/schema result и существующую семантику ошибок. Поток должен
давать thinking/text deltas без дополнительных LLM-вызовов, а
`rate_limit_event` — нормализованные 5h/7d `utilization` и `resets_at`.
Не полагайся на недокументированный polling API. Не допускай deadlock на
большом stdin, stderr/stdout или зависшем child; соблюдай timeout и корректно
завершай process tree.

## Качество и сдача

- Сначала проинвентаризируй, что реально сохранилось от оборванной попытки:
  transcript показывал задуманные `live.py`, streaming changes, `tui.py` и
  тесты, но часть tool writes могла не попасть на диск. Не доверяй transcript
  вместо файлов и не переписывай уже корректно сделанное.
- Добавь тесты для stream-json parser, quota normalization, atomic IPC,
  pause/wake/graceful-stop/kill, launcher argument mapping, attach/detach и
  ключевых Textual interactions (Textual Pilot там, где это надёжно).
- Проверь узкий набор тестов во время разработки, затем полный `make verify`.
- Соблюдай все правила `AGENTS.md`: команды через `nix develop -c`, не меняй
  gates/tier/progress rules, не используй xfail/skip как обход, не трогай
  чужую WIP, stage только явные пути, атомарные коммиты главного агента и
  зелёный `make verify` перед каждым кодовым коммитом.
- Раздели независимые логические изменения на атомарные коммиты (например,
  live streaming/IPC, backend controls, TUI/launcher), не смешивай с
  decompilation work текущего overnight-runner.
- В конце реально запусти безопасный smoke-test launcher/dashboard и attach к
  тестовому или текущему runner, проверь detach и graceful stop, обнови
  документацию/hand-off по правилам репозитория и сообщи пользователю команды
  запуска и результат `make verify`.

Задача завершена только когда TUI реализован, проверен и закоммичен; одного
плана, макета или частичной инфраструктуры недостаточно.
