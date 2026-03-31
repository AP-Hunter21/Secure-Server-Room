# 🛡️ Secure Server Room: IoT Data Ingestion & Anomaly Detection Pipeline
# Note: Codes are in 2nd branch
## 📖 Overview
This project is an end-to-end data pipeline that simulates, ingests, processes, and visualizes physical-world signals from a highly secure server room. It satisfies all requirements of the SAIG system architecture assignment.

The system simulates three continuous event streams (RFID Access, Camera Motion, and Temperature Sensors), normalizes the fragmented raw data into a strict schema, and applies real-time heuristic rules to flag critical anomalies (e.g., unauthorized access and cooling failures).

---

## 🏗️ System Architecture

* **Simulation Layer (`simulator.py`):** Generates realistic, jittered JSON payloads for 3 distinct physical devices.
* **Ingestion Layer (`ingestion.py`):** A FastAPI web server that receives POST requests, appends an ingestion timestamp, and buffers the raw stream to a local `.jsonl` file.
* **Processing Layer (`processor.py`):** A real-time worker that tails the stream buffer, normalizes the schemas, applies business rules to detect anomalies, and writes the structured records to SQLite.
* **Visualization Layer (`dashboard.py`):** A Streamlit web application providing a live, auto-refreshing dashboard of the processed database.

---

## 🧠 Anomaly Detection Rules (Heuristics)

* **Unauthorized Access Attempt:** Flags `True` with 99% confidence if an RFID badge is scanned and the hardware status returns as "REJECTED".
* **Critical Temperature Spike:** Flags `True` with 95% confidence if the server rack temperature probe exceeds 35.0°C.

---

## 🚀 Quick Start Guide

To run this pipeline locally, you will need to open multiple terminal windows to run the microservices simultaneously.

**1. Initialize the Database**
Run this once to create the required schema:
`python database.py`

**2. Start the Ingestion API**
In Terminal 1, start the FastAPI server:
`fastapi dev ingestion.py`

**3. Start the Data Processor**
In Terminal 2, start the worker that reads the stream:
`python processor.py`

**4. Start the Dashboard**
In Terminal 3, launch the Streamlit interface:
`streamlit
