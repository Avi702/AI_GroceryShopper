from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from agents import agents_pipeline
from db import init_db, get_latest_inventory, get_latest_shopping, get_scan_keys, save_scan
import anthropic
import base64
import boto3, os
from uuid import uuid4
from datetime import datetime

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
S3_BUCKET = os.getenv("S3_BUCKET")
app = FastAPI()

def upload_to_s3(image_bytes, content_type="image/jpeg"):

    key = f"scans/{datetime.utcnow():%Y%m%d-%H%M%S}-{uuid4().hex}.jpg"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,   # so it's served as an image, not a download
    )
    return key   # store/return this to reference the photo later

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
    try:
        key = await run_in_threadpool(upload_to_s3, image_bytes, image_file.content_type or "image/jpeg")
        if key:
            await run_in_threadpool(save_scan, key)
    except Exception as e:
        print(f"S3 upload/save failed: {e}")
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
    try:
        result = await run_in_threadpool(agents_pipeline, image_data)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return result


@app.get("/inventory")
async def get_inventory():
    items = await run_in_threadpool(get_latest_inventory)
    return {"items": items}


@app.get("/shopping")
async def get_shopping():
    list = await run_in_threadpool(get_latest_shopping)
    return {"shopping-list": list}

@app.get("/scans")
def get_scans():
    rows = get_scan_keys()   
    return {"scans": [
        {
            "url": s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": r["photo_key"]},
                ExpiresIn=3600,   
            ),
            "date": r["scanned_at"].strftime("%m/%d/%Y"),
            "time": r["scanned_at"].strftime("%I:%M %p"),
        }
        for r in rows
    ]}
