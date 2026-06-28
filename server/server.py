from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from agents import agents_pipeline
from db import init_db, save_inventory, get_latest_inventory
import anthropic
import base64


app = FastAPI()
# Create the inventory_items table on startup if it doesn't exist yet. Runs once
# when the server boots; idempotent thanks to CREATE TABLE IF NOT EXISTS.
init_db()
scan_requested = False

@app.post("/request-scan")      
def request_scan():
    global scan_requested
    scan_requested = True
    return {"status": "requested"}

@app.get("/scan-requested")       
def check_scan():
    return {"requested": scan_requested}

@app.post("/scan-done")          
def scan_done():
    global scan_requested
    scan_requested = False
    return {"status": "cleared"}

@app.post("/manualscan")
async def manual_scan(image_file: UploadFile):
    image_bytes = await image_file.read()
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
    try:
        result = await run_in_threadpool(agents_pipeline, image_data)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    print(result)

    # Persist the scanned inventory so it survives restarts and so GET /inventory
    # (and the Pi flow) can read it later. Wrapped in its own try so a database
    # hiccup doesn't discard a scan the user already spent API credits on.
    try:
        await run_in_threadpool(save_inventory, result["inventory"]["items"])
    except Exception as e:
        print(f"Failed to save inventory to DB: {e}")

    return result


@app.get("/inventory")
async def get_inventory():
    # Returns the most recent scan's items from the database, in the same shape as
    # /manualscan's inventory.items, so the frontend can render them identically.
    # run_in_threadpook ol because psycopg2 is synchronous (blocking) I/O.
    items = await run_in_threadpool(get_latest_inventory)
    return {"items": items}
