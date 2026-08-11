# Changelog

*(Ukrainian readers: this changelog is maintained in English only — see [README.uk.md](README.uk.md) for a Ukrainian project overview.)*
*(Українською: цей журнал змін ведеться лише англійською — див. [README.uk.md](README.uk.md) для огляду проєкту українською.)*

Versioning scheme: `epic.major.minor.fix` (e.g. `0.1.0.0`). `epic`/`major`
bump on deliberate, user-called milestones; day-to-day content additions
(a new skill, a skill update) bump `minor` by one and leave `fix` alone —
`e.m.(minor+1).f`. `fix` is reserved for a correction that adds no new
content (typo, broken link, wrong command).

## [0.1.0.0] - 2026-08-12
### Added
- Versioning (this file, `VERSION`).
- `migrator-new-task`: documented the `filter` field (Migrator ≥ 1.2.0) —
  when to use a raw `ГДЕ` condition on the main object instead of a full
  catalog mirror, and to check a candidate `related_catalogs` entry's row
  count (via `bridge_client.query_via_com()`, batched with `ОБЪЕДИНИТЬ
  ВСЕ`) before adding it as `reference_only`.
- `migrator-diagnose-write-rejection`: documented a second, unrelated
  failure signature — `ПредопределенноеЗначение()` "predefined item not
  found in the infobase data" (distinct from the business-rule `Записать()`
  rejection this skill already covered) — and that BridgeTool ≥ 1.3.0
  fixes it generally.
- Both found building the `bukovel-legacy:services` transfer task (see
  [Migrator](https://github.com/BusinessAutomationFramework/Migrator)
  1.2.0/1.3.0 and `baf-skills`' `classic-xml-bsl-gotchas`).
### Baseline (pre-dates versioning)
- `migrator-new-task`, `migrator-run-task`, `migrator-verify-transfer`,
  `migrator-diagnose-write-rejection`. See `README.md` for details.
