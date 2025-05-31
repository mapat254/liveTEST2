import streamlit as st
import os
import json
import datetime
from datetime import datetime
import time
from streaming_engine import RTMPStreamer
import threading

# Page config
st.set_page_config(
    page_title="YouTube RTMP Scheduler",
    page_icon="🎥",
    layout="wide"
)

# Initialize session state
if 'streams' not in st.session_state:
    st.session_state.streams = []
if 'streamer' not in st.session_state:
    st.session_state.streamer = RTMPStreamer()

# Title
st.title("YouTube RTMP Live Streaming Scheduler")

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Scheduled Streams")
    
    # Display current streams in a table
    if st.session_state.streams:
        streams_data = []
        for stream in st.session_state.streams:
            status = st.session_state.streamer.get_stream_status(stream['id']) or stream.get('status', 'Waiting')
            streams_data.append({
                'Video': os.path.basename(stream['video_path']),
                'Duration': stream['durasi'],
                'Start Time': stream['jam_mulai'],
                'Status': status
            })
        
        st.table(streams_data)
    else:
        st.info("No streams scheduled")

with col2:
    st.subheader("Schedule New Stream")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a video file", type=['mp4'])
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Time selection
        col_hour, col_minute = st.columns(2)
        with col_hour:
            hour = st.selectbox("Hour", range(24), format_func=lambda x: f"{x:02d}")
        with col_minute:
            minute = st.selectbox("Minute", range(60), format_func=lambda x: f"{x:02d}")
        
        # Duration
        duration = st.text_input("Duration (HH:MM:SS)", value="01:00:00")
        
        # Stream key
        stream_key = st.text_input("YouTube Stream Key", type="password")
        
        if st.button("Schedule Stream"):
            if stream_key:
                # Create new stream
                stream_id = len(st.session_state.streams) + 1
                stream = {
                    "id": stream_id,
                    "video_path": temp_path,
                    "durasi": duration,
                    "jam_mulai": f"{hour:02d}:{minute:02d}",
                    "streaming_key": stream_key,
                    "status": "Waiting"
                }
                
                st.session_state.streams.append(stream)
                st.success("Stream scheduled successfully!")
            else:
                st.error("Please enter a YouTube Stream Key")

# Background stream checker
def check_streams():
    while True:
        current_time = datetime.now()
        current_time_str = f"{current_time.hour:02d}:{current_time.minute:02d}"
        
        for stream in st.session_state.streams:
            if stream['jam_mulai'] == current_time_str and stream.get('status') == "Waiting":
                # Parse duration
                h, m, s = map(int, stream['durasi'].split(':'))
                duration_seconds = h * 3600 + m * 60 + s
                
                # Start the stream
                st.session_state.streamer.start_stream(
                    stream['id'],
                    stream['video_path'],
                    stream['streaming_key'],
                    duration_seconds
                )
                stream['status'] = "Live"
        
        time.sleep(30)

# Start background checker in a separate thread
if 'checker_thread' not in st.session_state:
    checker_thread = threading.Thread(target=check_streams, daemon=True)
    checker_thread.start()
    st.session_state.checker_thread = checker_thread

# Footer
st.markdown("---")
st.markdown("### Instructions")
st.markdown("""
1. Upload your video file (MP4 format)
2. Set the start time (hour and minute)
3. Set the duration in HH:MM:SS format
4. Enter your YouTube Stream Key
5. Click 'Schedule Stream' to add it to the schedule
""")