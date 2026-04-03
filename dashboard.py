import streamlit as st
import pandas as pd
import sqlite3
from streamlit_autorefresh import st_autorefresh

DB_FILE = "saig_events.db"
st.set_page_config(page_title="SAIG Facility Command", layout="wide")

# AUTO-REFRESH: Every 5 seconds
st_autorefresh(interval=5000, key="fencedashboard")

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM processed_events ORDER BY timestamp DESC", conn)
    conn.close()
    return df

st.title("🛡️ SAIG Facility Command Center")
# --- NEW: Admin Sidebar to Clear Logs ---
with st.sidebar:
    st.header("⚙️ Admin Controls")
    st.write("Reset the database to focus on live telemetry.")
    
    # We use type="primary" to make the button stand out (usually red/blue)
    if st.button("🗑️ Purge Database", type="primary"):
        import sqlite3
        try:
            # Connect to the DB and delete all rows
            conn = sqlite3.connect("saig_events.db")
            conn.execute("DELETE FROM processed_events")
            conn.commit()
            conn.close()
            
            st.success("Logs successfully cleared!")
            # Instantly force the dashboard to refresh and show 0s
            st.rerun() 
        except Exception as e:
            st.error(f"Error clearing logs: {e}")
df = load_data()

if not df.empty:
    # 1. REAL-TIME POP-UP (TOAST)
    latest = df.iloc[0]
    if latest['anomaly_flag'] == 1:
        st.toast(f"🚨 ALERT: {latest['event_type']} detected!", icon="🔥")

    # 2. VISUAL STATUS BANNER
    anomalies = df[df['anomaly_flag'] == 1]
    if not anomalies.empty and (pd.to_datetime('now', utc=True) - pd.to_datetime(anomalies.iloc[0]['timestamp'])).total_seconds() < 30:
        st.error(f"⚠️ CRITICAL THREAT ACTIVE: {anomalies.iloc[0]['event_type']} at {anomalies.iloc[0]['device_id']}")
    else:
        st.success("✅ FACILITY SECURE: All systems reporting normal operations.")

    # 3. METRIC CARDS
    m1, m2, m3 = st.columns(3)
    m1.metric("Telemetry Stream", f"{len(df)} events")
    m2.metric("Active Intrusions", len(anomalies[~anomalies['event_type'].str.contains("device_malfunction")]))
    m3.metric("System Health Alerts", len(anomalies[anomalies['event_type'].str.contains("device_malfunction")]))

    st.markdown("---")
    st.subheader("🗺️ Facility Spatial Heatmap")
    
    # Isolate threats from the last 60 seconds to make the heatmap dynamic
    recent_threats = df[(df['anomaly_flag'] == 1)].copy()
    recent_threats['time_diff'] = (pd.to_datetime('now', utc=True) - pd.to_datetime(recent_threats['timestamp'])).dt.total_seconds()
    active_threats = recent_threats[recent_threats['time_diff'] < 60]
    
    threat_devices = active_threats['device_id'].tolist()
    threat_locations = active_threats['location'].tolist()

    # Draw the 4 Zones
    z1, z2, z3, z4 = st.columns(4)
    zones = [("Zone 1 (North)", z1, "1"), ("Zone 2 (East)", z2, "2"), ("Zone 3 (South)", z3, "3"), ("Zone 4 (West)", z4, "4")]
    
    for zone_name, col, zone_id in zones:
        with col:
            # Check if this zone's ID is currently in the active threat list
            is_breached = any(zone_id in str(device) or zone_id in str(loc) for device, loc in zip(threat_devices, threat_locations))
            
            if is_breached:
                st.error(f"🚨 {zone_name}\n\n**BREACH DETECTED**")
            else:
                st.success(f"✅ {zone_name}\n\n**SECURE**")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🔴 Security Threat Feed")
        st.dataframe(anomalies[['timestamp', 'event_type', 'device_id']].head(10), use_container_width=True, hide_index=True)

    with c2:
        st.subheader("🚐 Service Center Dispatch (Auto-Call)")
        failures = anomalies[anomalies['event_type'].str.contains("device_malfunction")]
        if not failures.empty:
            dispatch = failures[['timestamp', 'device_id', 'event_type']].copy()
            dispatch['Status'] = "Technician Dispatched"
            st.dataframe(dispatch.head(5), use_container_width=True, hide_index=True)
        else:
            st.info("No active hardware malfunctions.")

    st.markdown("---")
    st.subheader("📋 Full System Logs")
    st.dataframe(df.head(50), use_container_width=True)

else:
    st.info("Awaiting initial telemetry from facility sensors...")