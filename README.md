**[English](README.md)** · [Українська](README.uk.md)

# migrator-skills

Claude Code skills for *operating* [Migrator](https://github.com/BusinessAutomationFramework/Migrator),
a schema-driven data migration tool for 1C:Enterprise / BAF infobases —
creating transfer tasks, running them safely, and rigorously verifying
the result. Complements `baf-skills` (general 1C/BSL knowledge), which
these don't duplicate.

## Skills

- [`migrator-new-task`](.claude/skills/migrator-new-task/SKILL.md) —
  step-by-step guide for creating a new transfer task: registering a
  task root, running `migrator suggest` for a `related_catalogs`
  starting point, writing the full `schema.yaml` (including the `filter`
  field, ≥ 1.2.0, for reading a known named subset instead of a whole
  catalog), validating, and a first limited smoke test.
- [`migrator-run-task`](.claude/skills/migrator-run-task/SKILL.md) —
  the discipline around actually running `python -m migrator run`
  safely: pre-flight checks against a stuck `1cv8.exe` session, schema
  validation before the ~20s BridgeTool cold start, timeout planning
  (each COM query — main *and* every cascade *and* every tabular part —
  costs a fixed ~20-30s regardless of row count), and how to read a
  partial-failure summary correctly.
- [`migrator-verify-transfer`](.claude/skills/migrator-verify-transfer/SKILL.md) —
  a reusable script (`scripts/verify_transfer.py`) that re-reads both
  the source and destination and reports missing/extra records,
  field-level differences (separating expected categories — group-record
  resets, the `Формат()` "empty date" serialization quirk — from real
  gaps), and a tabular-part row-count spot check. Don't trust a bare
  "Успешно: N" — this is what actually confirms a transfer worked.
- [`migrator-diagnose-write-rejection`](.claude/skills/migrator-diagnose-write-rejection/SKILL.md) —
  when the destination rejects a write with a business-rule error (not a
  parsing/COM bug): a targeted metadata dump of just the one object,
  finding its `ПередЗаписью`/`ОбработкаПроверкиЗаполнения` handlers, and
  checking whether they already respect the standard
  `ОбменДанными.Загрузка` import flag — found while diagnosing why the
  "Склады" acceptance test's `КассыККМ` cascade failed 0/159 for what
  turned out to be a one-line, general fix. Also covers the unrelated but
  similarly-shaped `ПредопределенноеЗначение()` "predefined item not found"
  signature (fixed generally in BridgeTool ≥ 1.3.0).

## Origin

Built alongside [Migrator](https://github.com/BusinessAutomationFramework/Migrator)
itself, generalizing the verification approach used for its "Склады"
catalog acceptance test.

## License

MIT — see `LICENSE`.
