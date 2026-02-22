"""Initialize PostgreSQL schema."""

from pathlib import Path

from wechat_alpha_mvp.database.models import Database


def main() -> None:
    db = Database()
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    with db.connect() as conn, conn.cursor() as cur:
        cur.execute(sql)


if __name__ == "__main__":
    main()
