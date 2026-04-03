import json
import time
import sqlite3
import uuid

RAW_STREAM_FILE = "raw_events.jsonl"
DB_FILE = "saig_events.db"
# Memory for Statistical Anomaly Detection
temperature_history = {}

def process_and_normalize(raw_event):
    event_id = str(uuid.uuid4())
    structured = {
        "event_id": event_id,
        "timestamp": raw_event.get("ts") or raw_event.get("time") or raw_event.get("timestamp") or "UNKNOWN",
        "device_id": "unknown",
        "device_type": "unknown",
        "location": "Main Facility",
        "event_type": "unknown",
        "anomaly_flag": 0,
        "confidence_score": 1.0,
        "raw_source_reference": json.dumps(raw_event)
    }

    # Business Rules Logic
    if raw_event.get("sensor_type") == "rfid_reader":
        structured.update({"device_id": raw_event.get("door_id"), "device_type": "access_control", "event_type": "badge_scan"})
        if raw_event.get("access_status") == "REJECTED":
            structured.update({"anomaly_flag": 1, "event_type": "unauthorized_access_attempt"})

    elif raw_event.get("device_class") == "perimeter_defense":
        structured.update({"device_id": raw_event.get("hardware_id"), "device_type": "electric_fence", "location": "Perimeter Wall", "event_type": "voltage_reading"})
        if raw_event.get("voltage", 7000) < 5000:
            structured.update({"anomaly_flag": 1, "event_type": "critical_perimeter_breach"})

    elif raw_event.get("system") == "health_monitor":
        structured.update({"device_id": raw_event.get("device_id"), "device_type": "security_camera", "event_type": "heartbeat_ping"})
        if raw_event.get("status") != "ONLINE":
            structured.update({"anomaly_flag": 1, "event_type": f"device_malfunction: {raw_event.get('status')}"})

    elif raw_event.get("sensor_type") == "power_monitor":
        structured.update({"device_id": raw_event.get("grid_location"), "device_type": "electrical_grid", "event_type": "power_reading"})
        volt = raw_event.get("voltage", 220)
        if volt < 200 or volt > 240:
            structured.update({"anomaly_flag": 1, "event_type": "severe_light_fluctuation"})
    
    # --- ADVANCED RULE 1: Tailgating (Sensor Fusion) ---
    elif raw_event.get("device_class") == "camera_motion":
        cam_id = raw_event.get("camera_id", "unknown_cam")
        structured["device_id"] = cam_id
        structured["device_type"] = "motion_sensor"
        structured["location"] = f"Zone {cam_id.split('_')[-1]}" if "_" in cam_id else "Interior"
        structured["event_type"] = "motion_detected"
        
        # Heuristic: If camera detects multiple people on a single badge swipe
        if raw_event.get("person_count", 1) > 1:
            structured["anomaly_flag"] = 1
            structured["event_type"] = f"tailgating_suspected ({raw_event['person_count']} people)"
            structured["confidence_score"] = 0.85

    # --- ADVANCED RULE 2: Statistical Anomaly Detection ---
    elif raw_event.get("hardware") == "temp_probe":
        probe = raw_event.get("probe_name", "unknown_probe")
        temp = raw_event.get("reading_celsius", 0)
        
        structured["device_id"] = probe
        structured["device_type"] = "environmental_sensor"
        structured["location"] = "Server Vault"
        structured["event_type"] = "temperature_reading"
        
        # 1. Update the moving average history
        if probe not in temperature_history:
            temperature_history[probe] = []
        
        history = temperature_history[probe]
        
        if len(history) >= 10:
            avg_temp = sum(history) / len(history)
            # Math Heuristic: Is the new reading 5 degrees higher than the recent average?
            if temp > avg_temp + 5.0:
                structured["anomaly_flag"] = 1
                structured["event_type"] = f"statistical_temp_spike (Avg was {round(avg_temp, 1)}C)"
            
            history.pop(0) # Keep the window sliding
            
        history.append(temp) # Add current reading to history
        
        # 2. Hardcoded failsafe (Original rule)
        if temp > 35.0 and structured["anomaly_flag"] == 0:
            structured["anomaly_flag"] = 1
            structured["event_type"] = "critical_temperature_spike"

    return structured

def save_to_db(event):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO processed_events VALUES (?,?,?,?,?,?,?,?,?)", list(event.values()))
    conn.commit()
    conn.close()

def trigger_external_webhook(event):
    """Simulates an API call to a 3rd party system like Slack, PagerDuty, or Twilio."""
    # We only page the guards for actual intrusions, not just offline cameras
    if "device_malfunction" not in event["event_type"]:
        print(f"🔔 [WEBHOOK FIRED] -> Paging Security Team via Slack: {event['event_type']} at {event['device_id']}!")

def run_processor():
    print("Processor Listening for Facility Telemetry...")
    with open(RAW_STREAM_FILE, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                event = process_and_normalize(json.loads(line))
                save_to_db(event)
                
                # Print visual feedback in the terminal (Correctly Indented)
                if event["anomaly_flag"]:
                    print(f"🚨 ANOMALY | {event['timestamp']} | {event['event_type']} | Device: {event['device_id']}")
                    # --- NEW: Trigger the external system (Slack/PagerDuty) ---
                    trigger_external_webhook(event)
                else:
                    print(f"✅ OK | {event['timestamp']} | {event['event_type']} | Device: {event['device_id']}")
            else:
                time.sleep(0.1)

if __name__ == "__main__":
    run_processor()