import time
import gspread
from gspread.utils import rowcol_to_a1
from .config import GOOGLE_SHEET_ID
from .google_services import get_google_credentials

def get_col_letter(col_idx: int) -> str:
    """Returns the column letter for a 1-based column index (e.g. 1 -> 'A', 12 -> 'L')."""
    return rowcol_to_a1(1, col_idx)[:-1]

def archive_deleted_rows() -> int:
    """
    Archives all rows with status 'Deleted' from Sheet1 to Sheet2.
    1. Reads Sheet1 and Sheet2.
    2. Identifies rows where Status == 'Deleted'.
    3. Appends deleted rows to the end of Sheet2 (expanding grid rows if necessary).
    4. Compacts active rows on Sheet1 to the top under the header.
    5. Clears trailing rows on Sheet1.
    """
    print("📦 Starting Deleted Rows Archiving (Sheet1 -> Sheet2)...")
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    try:
        ws1 = spreadsheet.worksheet("Sheet1")
    except Exception:
        ws1 = spreadsheet.sheet1

    try:
        ws2 = spreadsheet.worksheet("Sheet2")
    except Exception:
        worksheets = spreadsheet.worksheets()
        if len(worksheets) > 1:
            ws2 = worksheets[1]
        else:
            raise RuntimeError("Sheet2 not found in Google Spreadsheet.")

    val1 = ws1.get_all_values()
    val2 = ws2.get_all_values()

    if not val1:
        print("⚠️ Sheet1 is empty. Nothing to archive.")
        return 0

    header = val1[0]
    num_cols = len(header)
    col_letter = get_col_letter(num_cols)

    val1_data = [r for r in val1[1:] if any(cell.strip() for cell in r)]
    val2_data = [r for r in val2[1:] if any(cell.strip() for cell in r)]

    deleted_rows = []
    non_deleted_rows = []

    for r in val1_data:
        status = r[0].strip().lower() if r else ""
        if status == "deleted":
            deleted_rows.append(r)
        else:
            non_deleted_rows.append(r)

    print(f"   📊 Sheet1 total data rows: {len(val1_data)}")
    print(f"   🗑️ Rows marked 'Deleted' to move: {len(deleted_rows)}")
    print(f"   ✅ Active rows to remain on Sheet1: {len(non_deleted_rows)}")
    print(f"   📁 Sheet2 existing archived rows: {len(val2_data)}")

    if not deleted_rows:
        print("   ℹ️ No 'Deleted' rows found to archive. Sheet1 is already clean.")
        return 0

    # 1. Append deleted rows to Sheet2
    start_s2_row = len(val2_data) + 2  # +1 header, +1 1-based indexing
    end_s2_row = start_s2_row + len(deleted_rows) - 1
    total_s2_needed = end_s2_row + 10

    if ws2.row_count < total_s2_needed:
        add_count = total_s2_needed - ws2.row_count
        print(f"   Expanding Sheet2 grid by {add_count} rows...")
        ws2.add_rows(add_count)

    padded_deleted = [
        r + [""] * (num_cols - len(r)) if len(r) < num_cols else r[:num_cols]
        for r in deleted_rows
    ]

    range_s2 = f"A{start_s2_row}:{col_letter}{end_s2_row}"
    print(f"   Writing {len(deleted_rows)} rows to Sheet2 ({range_s2})...")
    ws2.update(range_name=range_s2, values=padded_deleted)
    print("   ✅ Sheet2 appended successfully.")

    # 2. Update Sheet1 with non-deleted rows
    if non_deleted_rows:
        padded_non_deleted = [
            r + [""] * (num_cols - len(r)) if len(r) < num_cols else r[:num_cols]
            for r in non_deleted_rows
        ]
        range_s1 = f"A2:{col_letter}{len(non_deleted_rows) + 1}"
        print(f"   Updating Sheet1 with {len(non_deleted_rows)} active rows ({range_s1})...")
        ws1.update(range_name=range_s1, values=padded_non_deleted)
        start_clear = len(non_deleted_rows) + 2
    else:
        start_clear = 2

    # 3. Clear trailing rows on Sheet1
    end_clear = len(val1_data) + 1
    if end_clear >= start_clear:
        range_clear = f"A{start_clear}:{col_letter}{end_clear}"
        print(f"   Clearing trailing rows on Sheet1 ({range_clear})...")
        ws1.batch_clear([range_clear])
        print("   ✅ Sheet1 trailing rows cleared.")

    print(f"\n🎉 Successfully archived {len(deleted_rows)} deleted rows from Sheet1 to Sheet2!")
    return len(deleted_rows)

if __name__ == "__main__":
    archive_deleted_rows()
