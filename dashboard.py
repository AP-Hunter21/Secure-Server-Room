import streamlit as st
import sqlite3
import pandas as pd

# Set up the page layout
st.set_page_config(page_title="SAIG Server Room Monitor", layout="wide")

st.title("🛡️ Secure Server Room: Live Monitoring Dashboard")
st.markdown("Real-time event logs and anomaly detection pipeline.")

def load_data():
    """Reads the structured data from our SQLite database."""
    conn = sqlite3.connect("saig_events.db")
    # Grab all events, newest first
    df = pd.read_sql_query("SELECT * FROM processed_events ORDER BY timestamp DESC", conn)
    conn.close()
    return df

# Load the data
df = load_data()

# Check if we have data yet
if df.empty:
    st.warning("⏳ Waiting for data... Ensure your simulator, API, and processor are running!")
else:
    # --- Top Level Metrics ---
    total_events = len(df)
    # SQLite stores booleans as 1 (True) and 0 (False)
    total_anomalies = len(df[df["anomaly_flag"] == 1]) 
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events Processed", total_events)
    col2.metric("Anomalies Detected", total_anomalies, delta_color="inverse")
    
    st.divider()
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("🚨 Critical Anomalies")
        anomalies_df = df[df["anomaly_flag"] == 1]
        if anomalies_df.empty:
            st.success("System Normal. No anomalies detected.")
        else:
            st.dataframe(
                anomalies_df[["timestamp", "device_type", "event_type", "confidence_score"]], 
                use_container_width=True, hide_index=True
            )

    with right_col:
        st.subheader("📊 Activity by Device")
        device_counts = df["device_type"].value_counts()
        st.bar_chart(device_counts)

    # --- Full Event Log ---
    st.divider()
    st.subheader("📝 Full Structured Event Log")
    st.caption("Displaying the exact mandatory schema.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Refresh button
    if st.button("🔄 Refresh Dashboard to see latest data"):
        st.rerun()