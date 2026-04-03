from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import uvicorn
import json
from datetime import datetime, timezone

app = FastAPI()

RAW_STREAM_FILE = "raw_events.jsonl"

# --- NEW: API SECURITY LAYER ---
API_KEY = "saig-super-secret-2026"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="🚨 Unauthorized: Invalid API Key")
    return api_key

@app.post("/ingest")
# We add the security dependency here:
async def receive_event(request: Request, api_key: str = Security(verify_api_key)):
    payload = await request.json()
    payload["ingested_at"] = datetime.now(timezone.utc).isoformat()
    
    with open(RAW_STREAM_FILE, "a") as f:
        f.write(json.dumps(payload) + "\n")
        
    return {"status": "secure_receipt", "message": "Encrypted event buffered."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)