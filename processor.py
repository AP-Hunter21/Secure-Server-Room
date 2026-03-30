import json
import time
import uuid
import sqlite3

RAW_STREAM_FILE = "raw_events.jsonl"
DB_NAME = "saig_events.db"

def process_and_normalize(raw_event):
    """
    Transforms messy raw signals into the strict output schema
    and applies simple rules to detect anomalies.
    """
    # 1. Initialize the mandatory schema
    structured = {
        "event_id": str(uuid.uuid4()),
        "timestamp": None,
        "device_id": None,
        "device_type": None,
        "location": "Secure Server Room A",
        "event_type": None,
        "anomaly_flag": False,
        "confidence_score": 1.0, 
        "raw_source_reference": json.dumps(raw_event)
    }

    # 2. Normalization & Anomaly Detection
    
    # Handle RFID Reader
    if "sensor_type" in raw_event and raw_event["sensor_type"] == "rfid_reader":
        structured["timestamp"] = raw_event.get("ts")
        structured["device_id"] = raw_event.get("door_id")
        structured["device_type"] = "access_control"
        structured["event_type"] = "badge_scan"
        
        # Anomaly Rule 1: Unauthorized access attempt
        if raw_event.get("access_status") == "REJECTED":
            structured["anomaly_flag"] = True
            structured["confidence_score"] = 0.99
            structured["event_type"] = "unauthorized_access_attempt"

    # Handle Camera Motion
    elif "device_class" in raw_event and raw_event["device_class"] == "camera_motion":
        structured["timestamp"] = raw_event.get("timestamp")
        structured["device_id"] = raw_event.get("camera_id")
        structured["device_type"] = "motion_sensor"
        structured["event_type"] = "motion_detected"

    # Handle Temperature Sensor
    elif "hardware" in raw_event and raw_event["hardware"] == "temp_probe":
        structured["timestamp"] = raw_event.get("time")
        structured["device_id"] = raw_event.get("probe_name")
        structured["device_type"] = "environmental_sensor"
        structured["event_type"] = "temperature_reading"
        
        # Anomaly Rule 2: Cooling failure (Temp > 35.0 C)
        temp = raw_event.get("reading_celsius", 0)
        if temp > 35.0:
            structured["anomaly_flag"] = True
            structured["confidence_score"] = 0.95
            structured["event_type"] = "critical_temperature_spike"

    return structured

def save_to_db(event_dict):
    """Inserts the structured record into SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO processed_events 
        (event_id, timestamp, device_id, device_type, location, event_type, anomaly_flag, confidence_score, raw_source_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        event_dict["event_id"], event_dict["timestamp"], event_dict["device_id"],
        event_dict["device_type"], event_dict["location"], event_dict["event_type"],
        event_dict["anomaly_flag"], event_dict["confidence_score"], event_dict["raw_source_reference"]
    ))
    conn.commit()
    conn.close()

def run_processor():
    """Continuously reads the stream buffer in real-time."""
    print("🧠 Starting Data Processor... Waiting for real-time events.")
    
    try:
        # Open the raw file to read from it
        with open(RAW_STREAM_FILE, "r") as f:
            # Jump to the end of the file so we only process new events
            f.seek(0, 2) 
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5) # Wait briefly if no new data has arrived
                    continue
                
                # Process the new line
                raw_event = json.loads(line)
                structured_event = process_and_normalize(raw_event)
                save_to_db(structured_event)
                
                # Print visual feedback in the terminal
                status = "🚨 ANOMALY" if structured_event["anomaly_flag"] else "✅ OK"
                print(f"{status} | {structured_event['timestamp']} | {structured_event['event_type']} | Device: {structured_event['device_id']}")
                
    except KeyboardInterrupt:
        print("\n🛑 Processor stopped.")
    except FileNotFoundError:
        print("❌ Error: raw_events.jsonl not found. Make sure ingestion.py is running and receiving data.")

if __name__ == "__main__":
    run_processor()