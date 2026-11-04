"""
Command line version (no web app needed).

Examples:
    python cli.py samples/hdfc_text.pdf
    python cli.py samples/axis_locked.pdf --password AXIS1234 --out axis.xlsx
    python cli.py jan.pdf feb.pdf mar.pdf --out q1.csv
"""

import argparse
from pathlib import Path

from src.exporter import to_csv_bytes, to_excel_bytes
from src.pipeline import combined_report, process_many


def main():
    parser = argparse.ArgumentParser(description="Extract and classify bank statement transactions.")
    parser.add_argument("pdfs", nargs="+", help="one or more bank statement PDFs")
    parser.add_argument("--password", help="password for locked PDFs")
    parser.add_argument("--out", default="classified_transactions.xlsx", help="output .xlsx or .csv file")
    args = parser.parse_args()

    files = [(Path(p).name, Path(p).read_bytes(), args.password) for p in args.pdfs]
    output = process_many(files)
    table = output["merged"]
    report = combined_report(output["results"], table)

    for result in output["results"]:
        acc, rep = result["account"], result["report"]
        print(f"\n{acc['file_name']}: {acc['bank_name']} | {acc.get('account_holder')} | "
              f"A/c {acc.get('account_number')} | IFSC {acc.get('ifsc')} | PDF type: {acc['pdf_type']}")
        print(f"  {rep['transaction_count']} transactions, balance check {rep['balance_check_pass_rate']}%")
        for problem in rep["problems"]:
            print("  !", problem)

    out = Path(args.out)
    if out.suffix.lower() == ".csv":
        out.write_bytes(to_csv_bytes(table))
    else:
        out.write_bytes(to_excel_bytes(table, output["results"][0]["account"], report))
    print(f"\nCategories:\n{table['category'].value_counts().to_string()}")
    print(f"\nSaved {len(table)} rows to {out}")


if __name__ == "__main__":
    main()
