#!/usr/bin/env python3
"""
Generate an Excel .xlsx test file from the CSV dataset.

Input:  db/seed_demo_orders_test.csv
Output: db/seed_demo_orders_test.xlsx

Headers: order_no, group_code, weight_kg, status, shipping_fee
"""

import csv
from pathlib import Path
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
CSV_IN = ROOT / "db" / "seed_demo_orders_test.csv"
XLSX_OUT = ROOT / "db" / "seed_demo_orders_test.xlsx"


def to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def main():
    if not CSV_IN.exists():
        raise SystemExit(f"CSV not found: {CSV_IN}")

    wb = Workbook()
    ws = wb.active
    ws.title = "orders"

    headers = ["order_no", "group_code", "weight_kg", "status", "shipping_fee"]
    ws.append(headers)

    with CSV_IN.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ws.append([
                (row.get("order_no") or "").strip(),
                (row.get("group_code") or "").strip() or None,
                to_float(row.get("weight_kg")),
                (row.get("status") or "").strip(),
                to_float(row.get("shipping_fee")),
            ])

    wb.save(str(XLSX_OUT))
    print(f"Wrote {XLSX_OUT}")


if __name__ == "__main__":
    main()

