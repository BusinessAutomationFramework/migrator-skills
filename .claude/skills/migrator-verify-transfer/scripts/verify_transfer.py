"""
Рігорозна перевірка результату переносу Migrator: польове порівняння
джерело/приймач для головного довідника/документа завдання, плюс
вибіркова перевірка кількості рядків табличних частин (якщо заявлені).

НЕ покладайтесь лише на "Успешно: N" з виводу `migrator run` - ця
перевірка читає ОБИДВІ бази заново і звіряє факти.

Використання:
    python verify_transfer.py <шлях_до_Migrator> <корінь>:<завдання> [--ts-sample N] [--limit N]

Приклад:
    python verify_transfer.py D:\\Bukovel\\BAF_TOOLS\\Migrator bukovel-legacy:warehouse --ts-sample 15
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("migrator_root", help="Шлях до кореня репозиторію Migrator")
    parser.add_argument("task", help="<корінь>:<завдання>")
    parser.add_argument("--ts-sample", type=int, default=15, help="Скільки записів вибірково перевіряти для табличних частин (за замовч. 15)")
    parser.add_argument("--limit", type=int, default=None, help="Обмежити перевірку N записами (для великих довідників)")
    args = parser.parse_args()

    migrator_root = Path(args.migrator_root).resolve()
    sys.path.insert(0, str(migrator_root))
    sys.path.insert(0, str(migrator_root / "BridgeTool"))

    from migrator.config import resolve_schema_path
    from migrator.schema import load_schema
    import bridge_client

    schema = load_schema(resolve_schema_path(args.task))
    ts_names = schema.tabular_part_names

    print(f"Завдання: {args.task} ({schema.kind}.{schema.name})")
    print(f"Табличні частини у схемі: {ts_names or '(немає)'}")

    print("\nЧитання джерела через COM...")
    src_query = schema.select_query(limit=args.limit)
    src_rows = bridge_client.query_via_com(
        schema.source.connection_string, src_query,
        tabular_parts=ts_names or None,
        object_ref=schema.object_ref if ts_names else None,
        timeout=300,
    )
    src_by_uuid = {r["Ссылка"]["__ref_uuid__"]: r for r in src_rows if isinstance(r.get("Ссылка"), dict)}
    print(f"Джерело: {len(src_by_uuid)} записів.")

    dest = bridge_client.Bridge1C(
        platform_exe=schema.destination.platform_exe or bridge_client.DEV.platform_exe,
        connect_args=schema.destination.connect_args or bridge_client.DEV.connect_args,
    )

    print("Читання приймача через BridgeTool...")
    with dest:
        dest_query = f"ВЫБРАТЬ {'ПЕРВЫЕ ' + str(args.limit) + ' ' if args.limit else ''}* ИЗ {schema.object_ref}"
        result = dest.call_expression(f'ВыполнитьЗапрос("{dest_query}")', timeout=300)
        if not result.get("ok"):
            print(f"ПОМИЛКА читання приймача: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
        dest_rows = result["value"]
        dest_by_uuid = {r["Ссылка"]["__ref_uuid__"]: r for r in dest_rows if isinstance(r.get("Ссылка"), dict)}
        print(f"Приймач: {len(dest_by_uuid)} записів.")

        missing = set(src_by_uuid) - set(dest_by_uuid)
        extra = set(dest_by_uuid) - set(src_by_uuid)
        print(f"\nВідсутні у приймачі (є в джерелі): {len(missing)}")
        for u in list(missing)[:10]:
            print(f"  {u} {src_by_uuid[u].get('Наименование', '?')}")
        print(f"Зайві у приймачі (немає в джерелі): {len(extra)}")
        for u in list(extra)[:10]:
            print(f"  {u} {dest_by_uuid[u].get('Наименование', '?')}")
        if missing or extra:
            print(
                "  (якщо джерело - живий, спільний сервер - це може бути дрейф "
                "даних між моментом переносу і моментом цієй перевірки, а не помилка коду)"
            )

        # Польове порівняння - виключаємо табличні частини (окрема
        # вибіркова перевірка нижче) і ВерсияДанных (платформа сама
        # оновлює при кожному записі, завжди відрізняється).
        ignore_fields = {"ВерсияДанных"} | set(ts_names)
        field_diffs = {}
        group_diffs = {}
        for uuid, src_row in src_by_uuid.items():
            dest_row = dest_by_uuid.get(uuid)
            if not dest_row:
                continue
            is_group = bool(src_row.get("ЭтоГруппа"))
            for key, src_val in src_row.items():
                if key in ignore_fields:
                    continue
                dest_val = dest_row.get(key)
                if src_val != dest_val:
                    bucket = group_diffs if is_group else field_diffs
                    bucket.setdefault(key, []).append((uuid, src_val, dest_val))

        print(f"\nВідмінності полів (НЕ групові записи) - {len(field_diffs)} полів із відмінністю:")
        for key, diffs in field_diffs.items():
            print(f"  {key}: {len(diffs)} відмінностей, напр. {diffs[0]}")
        print(
            f"\nВідмінності полів у ГРУПОВИХ записах - {len(group_diffs)} полів "
            "(ОЧІКУВАНО: платформа скидає більшість атрибутів для груп, це не помилка):"
        )
        for key in list(group_diffs)[:5]:
            print(f"  {key}: {len(group_diffs[key])} відмінностей (групи)")

        if ts_names:
            print(f"\nВибіркова перевірка табличних частин (перших {args.ts_sample} НЕ-групових записів):")
            sample = [r for r in src_rows if not r.get("ЭтоГруппа")][: args.ts_sample]
            mismatches = 0
            for row in sample:
                uuid = row["Ссылка"]["__ref_uuid__"]
                if uuid not in dest_by_uuid:
                    continue
                for ts_name in ts_names:
                    src_count = len(row.get(ts_name, []))
                    r = dest.call_expression(
                        f'Справочники["{schema.name}"].ПолучитьСсылку(Новый УникальныйИдентификатор("{uuid}"))'
                        f'.ПолучитьОбъект().{ts_name}.Количество()',
                        timeout=30,
                    )
                    dest_count = r.get("value") if r.get("ok") else f"ERROR:{r.get('error')}"
                    if src_count != dest_count:
                        mismatches += 1
                        print(f"  MISMATCH {uuid} {ts_name}: джерело={src_count} приймач={dest_count}")
            print(f"Розбіжностей табличних частин: {mismatches} з {len(sample) * len(ts_names)} перевірених.")

    print("\nЗавершено.")


if __name__ == "__main__":
    main()
