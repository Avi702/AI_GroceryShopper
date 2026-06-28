import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
load_dotenv()
HOST = os.getenv('DB_HOST')
PORT = int(os.getenv('DB_PORT'))
DB = os.getenv('DB_NAME')
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')

def get_connection():
    return psycopg2.connect(
        host=HOST, port=PORT, database=DB, user=USER,
        password=PASSWORD, sslmode='require',
        connect_timeout=10,  
    )

def init_db():
    """Create the inventory_items table if it doesn't already exist.

    Called once on server startup. `IF NOT EXISTS` makes it idempotent — running
    it on every boot is harmless; it only actually creates the table the first time.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id          SERIAL PRIMARY KEY,   -- auto-incrementing row id
                    name        TEXT NOT NULL,        -- e.g. "Peanut Butter"
                    amount      INTEGER,              -- how many units detected
                    confidence  REAL,                 -- 0-1 detection confidence
                    image_url   TEXT,                 -- product photo URL
                    scanned_at  TIMESTAMPTZ NOT NULL  -- when this scan happened
                );
                """
            )
        conn.commit()  # DDL (CREATE TABLE) only persists after a commit
    finally:
        conn.close()   # always hand the connection back, even if something failed


def save_inventory(items):
    """Insert every item from one scan, all tagged with one shared timestamp.

    `items` is the list of dicts agents_pipeline produces (name / amount /
    confidence / image_url). Giving the whole batch a single `scanned_at` is what
    lets us later pull back "the most recent scan" as a group. Returns that timestamp.
    """
    scanned_at = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # executemany runs the same INSERT once per item. The %(key)s placeholders
            # are filled from each dict, and psycopg2 safely escapes the values —
            # which is what prevents SQL injection. Never build SQL with f-strings/+.
            cur.executemany(
                """
                INSERT INTO inventory_items (name, amount, confidence, image_url, scanned_at)
                VALUES (%(name)s, %(amount)s, %(confidence)s, %(image_url)s, %(scanned_at)s)
                """,
                [
                    {
                        "name": it["name"],
                        "amount": it.get("amount"),
                        "confidence": it.get("confidence"),
                        "image_url": it.get("image_url"),
                        "scanned_at": scanned_at,
                    }
                    for it in items
                ],
            )
        conn.commit()  # nothing is actually written to the DB until we commit
    finally:
        conn.close()
    return scanned_at


def get_latest_inventory():
    """Return the items from the most recent scan, in the frontend's item shape.

    "Most recent scan" = every row whose scanned_at equals the largest scanned_at
    in the table. Each row is reshaped back into the exact object ReportCard wants:
    name, amount, confidence, image_url, date, time.
    """
    conn = get_connection()
    try:
        # RealDictCursor returns each row as a dict ({"name": ...}) instead of a
        # positional tuple, so we can read columns by name below.
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, amount, confidence, image_url, scanned_at
                FROM inventory_items
                WHERE scanned_at = (SELECT MAX(scanned_at) FROM inventory_items)
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    # Turn the stored timestamp back into the date/time strings the card displays.
    items = []
    for r in rows:
        ts = r["scanned_at"]
        items.append({
            "name": r["name"],
            "amount": r["amount"],
            "confidence": r["confidence"],
            "image_url": r["image_url"],
            "date": ts.strftime("%m/%d/%Y"),
            "time": ts.strftime("%I:%M %p"),
        })
    return items


if __name__ == "__main__":
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT version();')
            print(cur.fetchone()[0])
    finally:
        conn.close()
