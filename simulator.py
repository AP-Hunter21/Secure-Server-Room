import json
import time
import random
import requests
from datetime import datetime, timezone

# We will send our data to this local address (we will build the API in the next step!)
API_ENDPOINT = "http://127.0.0.1:8000/ingest"

def get_current_time():
    """Returns current time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()

def generate_access_event():
    """Simulates an RFID badge reader at the server room door."""
    employees = ["EMP_001", "EMP_002", "EMP_003", "UNKNOWN_BADGE"]
    emp = random.choice(employees)
    # If it's an unknown badge, the status is REJECTED
    status = "REJECTED" if emp == "UNKNOWN_BADGE" else "GRANTED"
    
    return {
        "sensor_type": "rfid_reader",
        "door_id": "door_srv_01",
        "employee_id": emp,
        "access_status": status,
        "ts": get_current_time() # Notice the time key is 'ts'
    }

def generate_motion_event():
    """Simulates a camera detecting motion inside the server room."""
    return {
        "device_class": "camera_motion",
        "camera_id": "cam_inside_01",
        "motion_active": True,
        "timestamp": get_current_time() # Notice the time key is 'timestamp'
    }

def generate_temperature_event():
    """Simulates a temperature sensor on the server racks."""
    # Normal temp is around 20-25°C. We occasionally spike it to simulate a cooling failure.
    is_spike = random.random() < 0.1 # 10% chance of a heat spike anomaly
    temp = round(random.uniform(35.0, 45.0) if is_spike else random.uniform(18.0, 26.0), 2)
    
    return {
        "hardware": "temp_probe",
        "probe_name": "rack_A_temp",
        "reading_celsius": temp,
        "time": get_current_time() # Notice the time key is 'time'
    }

def run_simulator():
    """The main loop that continuously generates and sends device signals."""
    print("🚀 Starting Secure Server Room Device Simulator...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # 1. Randomly pick which device is sending a signal right now
            event_generator = random.choice([
                generate_access_event, 
                generate_motion_event, 
                generate_temperature_event
            ])
            
            # 2. Generate the raw payload
            raw_payload = event_generator()
            
            # 3. Print it to the console so we can see it working
            print(f"📡 Emitting: {json.dumps(raw_payload)}")
            
            # 4. Attempt to send it to our API (we will catch the error if the API isn't built yet)
            try:
                requests.post(API_ENDPOINT, json=raw_payload, timeout=2)
            except requests.exceptions.ConnectionError:
                # API is down or not built yet, we just pass for now
                pass
            
            # 5. Wait for a random short interval before the next signal (0.5 to 2.5 seconds)
            time.sleep(random.uniform(0.5, 2.5))
            
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user.")

if __name__ == "__main__":
    run_simulator()