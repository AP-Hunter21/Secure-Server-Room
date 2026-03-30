from fastapi import FastAPI, Request
from datetime import datetime, timezone
import json

# Initialize the API
app = FastAPI(title="SAIG Ingestion API")

# We will use this file as a simple "message queue" to hold our raw stream.
# Our processing script will read from this later.
RAW_STREAM_FILE = "raw_events.jsonl"

@app.post("/ingest")
async def receive_event(request: Request):
    """
    Receives physical device signals, timestamps them, 
    and forwards them to the processing buffer.
    """
    # 1. Receive the raw event data
    raw_payload = await request.json()
    
    # 2. Add an ingestion timestamp (Mandatory Requirement)
    # The device has its own timestamp, but we log exactly when our system received it.
    raw_payload["ingested_at"] = datetime.now(timezone.utc).isoformat()
    
    # 3. Forward to the processing layer 
    # We append it to a JSON Lines file which acts as our stream buffer.
    with open(RAW_STREAM_FILE, "a") as f:
        f.write(json.dumps(raw_payload) + "\n")
        
    # Print to console so we can visually confirm receipt
    # We use a bit of logic to guess the device type for the print statement
    device_hint = raw_payload.get("sensor_type", 
                  raw_payload.get("device_class", 
                  raw_payload.get("hardware", "Unknown Device")))
                  
    print(f"✅ Successfully ingested signal from: {device_hint}")
    
    return {"status": "received", "ingested_at": raw_payload["ingested_at"]}

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    print("🟢 Starting Ingestion API on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
