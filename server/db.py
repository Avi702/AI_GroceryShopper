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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shopping_list (
                  id SERIAL PRIMARY KEY,
                  name TEXT NOT NULL,
                  amount INTEGER,
                  store TEXT NOT NULL,
                  link TEXT NOT NULL,
                  price NUMERIC NOT NULL,
                  generated_at TIMESTAMPTZ NOT NULL
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                id          SERIAL PRIMARY KEY,
                photo_key   TEXT NOT NULL,
                scanned_at  TIMESTAMPTZ NOT NULL
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
        conn.commit()
    finally:
        conn.close()
    delete_old_inventory()
    delete_old_shopping()
    return scanned_at


def save_shopping(items):
    """Insert the shop results as one shopping list under a single generated_at."""
    generated_at = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO shopping_list (name, amount, store, link, price, generated_at)
                VALUES (%(name)s, %(amount)s, %(store)s, %(link)s, %(price)s, %(generated_at)s)
                """,
                [
                    {
                        "name": it["name"],
                        "amount": it.get("amount"),
                        "store": it["store"],
                        "link": it["link"],
                        "price": it["price"],
                        "generated_at": generated_at,
                    }
                    for it in items
                ],
            )
        conn.commit()
    finally:
        conn.close()
    return generated_at


def save_scan(photo_key):
    """Record a captured photo's S3 key so /scans can list it later."""
    scanned_at = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scans (photo_key, scanned_at) VALUES (%s, %s)",
                (photo_key, scanned_at),
            )
        conn.commit()
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

def get_inventory_history():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, amount, scanned_at FROM inventory_items ORDER BY scanned_at
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [
        {"name": r["name"], "amount": r["amount"], "scanned_at": r["scanned_at"].isoformat()}
        for r in rows
    ]

def get_latest_shopping():
    """Return the items from the most recent shopping list (largest generated_at).

    Same "latest batch" trick as get_latest_inventory, but against the
    shopping_list table and returning the shop fields (store / link / price).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, amount, store, link, price, generated_at
                FROM shopping_list
                WHERE generated_at = (SELECT MAX(generated_at) FROM shopping_list)
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    items = []
    for r in rows:
        ts = r["generated_at"]
        items.append({
            "name": r["name"],
            "amount": r["amount"],
            "store": r["store"],
            "link": r["link"],
            # NUMERIC comes back as a Decimal — cast to float so it serializes
            # to a plain JSON number.
            "price": float(r["price"]),
            "date": ts.strftime("%m/%d/%Y"),
            "time": ts.strftime("%I:%M %p"),
        })
    return items




def delete_old_inventory(days=3):
    """Delete inventory_items older than `days` days, keeping only the recent window.

    `scanned_at < now() - (days * interval '1 day')` removes anything past the
    cutoff. `days` is parameterized (%s), never string-formatted into the SQL.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM inventory_items WHERE scanned_at < now() - (%s * interval '1 day')",
                (days,),
            )
        conn.commit()  # a DELETE only takes effect after commit
    finally:
        conn.close()


def delete_old_shopping(days=3):
    """Delete shopping_list rows older than `days` days, keeping only the recent window."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM shopping_list WHERE generated_at < now() - (%s * interval '1 day')",
                (days,),
            )
        conn.commit()
    finally:
        conn.close()

def get_scan_keys(limit=50):
    """Return recent scan photo keys, newest first, for the Scans page.

    Leaves scanned_at as a datetime (NOT stringified) because the /scans
    endpoint calls .strftime() on it.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT photo_key, scanned_at
                FROM scans
                ORDER BY scanned_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return rows

if __name__ == "__main__":
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT version();')
            print(cur.fetchone()[0])
    finally:
        conn.close()
