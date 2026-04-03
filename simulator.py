import time
import json
import random
import requests
from datetime import datetime, timezone

# --- MY FIX: Docker uses the container name 'api' instead of 127.0.0.1 ---
API_URL = "http://api:8000/ingest"

def get_current_time():
    return datetime.now(timezone.utc).isoformat()

def generate_access_event():
    employees = ["EMP_001", "EMP_002", "EMP_003", "UNKNOWN_BADGE"]
    emp = random.choices(employees, weights=[30, 30, 30, 4], k=1)[0]
    status = "GRANTED" if emp != "UNKNOWN_BADGE" else "REJECTED"
    return {
        "sensor_type": "rfid_reader",
        "door_id": f"door_zone_{random.randint(1, 4)}",
        "employee_id": emp,
        "access_status": status,
        "ts": get_current_time()
    }

def generate_motion_event():
    persons = 1 if random.random() > 0.05 else random.choice([2, 3])
    zone = random.randint(1, 4)
    return {
        "device_class": "camera_motion",
        "camera_id": f"cam_zone_{zone}",
        "motion_active": True,
        "person_count": persons,
        "timestamp": get_current_time()
    }

def generate_temperature_event():
    reading = random.uniform(18.0, 26.0)
    if random.random() < 0.03: 
        reading = random.uniform(35.0, 45.0)
    return {
        "hardware": "temp_probe",
        "probe_name": f"rack_{random.choice(['A', 'B', 'C', 'D'])}_temp",
        "reading_celsius": round(reading, 2),
        "time": get_current_time()
    }

def generate_fence_event():
    voltage = random.uniform(6800.0, 7200.0)
    if random.random() < 0.02:
        voltage = random.uniform(0.0, 4500.0)
    return {
        "device_class": "perimeter_defense",
        "hardware_id": f"fence_zone_{random.randint(1, 4)}",
        "voltage": round(voltage, 2),
        "timestamp": get_current_time()
    }

def generate_heartbeat_event():
    status = "ONLINE"
    if random.random() < 0.02:
        status = random.choice(["OFFLINE", "LENS_COVERED", "POWER_LOSS"])
    return {
        "system": "health_monitor",
        "device_id": f"cam_ext_{random.randint(1, 15)}",
        "status": status,
        "time": get_current_time()
    }

def generate_power_event():
    voltage = random.uniform(218.0, 222.0)
    if random.random() < 0.03: 
        voltage = random.choice([180.0, 260.0]) 
    return {
        "sensor_type": "power_monitor",
        "grid_location": f"Zone_{random.randint(1, 4)}_Mains",
        "voltage": round(voltage, 2),
        "timestamp": get_current_time()
    }

def run_simulator():
    print("Starting Realistic Facility Simulator...")
    event_generators = [
        generate_access_event, generate_motion_event, 
        generate_temperature_event, generate_fence_event,
        generate_heartbeat_event, generate_power_event
    ]
    
    while True:
        event_func = random.choice(event_generators)
        payload = event_func()
        try:
            # --- The API Key Bouncer VIP Pass ---
            HEADERS = {"X-API-Key": "saig-super-secret-2026"}
            requests.post(API_URL, json=payload, headers=HEADERS)
            print(f"Emitting telemetry from {payload.get('device_id', 'Sensor')}...")
        except Exception as e:
            print(f"Connection failed: {e}")
            
        time.sleep(random.uniform(1.5, 3.0))

if __name__ == "__main__":
    run_simulator()