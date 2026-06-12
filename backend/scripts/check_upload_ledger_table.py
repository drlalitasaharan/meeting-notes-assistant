import os

import sqlalchemy as sa


def main() -> int:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("FAIL: DATABASE_URL is not set.")
        return 1

    engine = sa.create_engine(database_url)
    inspector = sa.inspect(engine)

    if "upload_ledger" not in inspector.get_table_names():
        print("FAIL: upload_ledger table does not exist.")
        return 1

    columns = {col["name"] for col in inspector.get_columns("upload_ledger")}

    required_columns = {
        "id",
        "user_id",
        "account_id",
        "meeting_id",
        "original_filename",
        "file_size_bytes",
        "content_type",
        "storage_key",
        "status",
        "counted_at",
        "created_at",
        "updated_at",
        "deleted_at",
    }

    missing = sorted(required_columns - columns)

    if missing:
        print(f"FAIL: upload_ledger missing columns: {missing}")
        return 1

    print("PASS: upload_ledger table exists with required columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
