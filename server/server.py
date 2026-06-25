from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from agents import agents_pipeline
import anthropic
import base64


app = FastAPI()
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
    return result
