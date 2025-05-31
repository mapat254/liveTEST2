import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
import threading
import time
import json

class StreamingScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Streaming Scheduler")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        
        # Data structure to store streaming tasks
        self.streams = []
        self.stream_threads = {}
        
        # Load saved streams if available
        self.load_streams()
        
        self.create_ui()
        
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Live Streaming Scheduler", font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview (Table)
        columns = ("index", "video", "durasi", "jam_mulai", "streaming_key", "status", "aksi")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.tree.heading("index", text="#")
        self.tree.heading("video", text="Video")
        self.tree.heading("durasi", text="Durasi")
        self.tree.heading("jam_mulai", text="Jam Mulai")
        self.tree.heading("streaming_key", text="Streaming Key")
        self.tree.heading("status", text="Status")
        self.tree.heading("aksi", text="Aksi")
        
        self.tree.column("index", width=30, anchor=tk.CENTER)
        self.tree.column("video", width=150)
        self.tree.column("durasi", width=80, anchor=tk.CENTER)
        self.tree.column("jam_mulai", width=80, anchor=tk.CENTER)
        self.tree.column("streaming_key", width=200)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        self.tree.column("aksi", width=80, anchor=tk.CENTER)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Video path
        ttk.Label(input_frame, text="Path video").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.video_path_var = tk.StringVar()
        video_path_entry = ttk.Entry(input_frame, textvariable=self.video_path_var, width=30)
        video_path_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Browse button
        browse_btn = ttk.Button(input_frame, text="Pilih Video", command=self.browse_video)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Time selection
        ttk.Label(input_frame, text="Jam").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Hours
        self.hour_var = tk.StringVar()
        hour_options = [f"{i:02d}" for i in range(24)]
        hour_dropdown = ttk.Combobox(input_frame, textvariable=self.hour_var, values=hour_options, width=5)
        hour_dropdown.current(datetime.datetime.now().hour)
        hour_dropdown.grid(row=0, column=4, padx=5, pady=5)
        
        # Minutes
        ttk.Label(input_frame, text=":").grid(row=0, column=5)
        self.minute_var = tk.StringVar()
        minute_options = [f"{i:02d}" for i in range(60)]
        minute_dropdown = ttk.Combobox(input_frame, textvariable=self.minute_var, values=minute_options, width=5)
        minute_dropdown.current(datetime.datetime.now().minute)
        minute_dropdown.grid(row=0, column=6, padx=5, pady=5)
        
        # Duration
        ttk.Label(input_frame, text="Durasi (hh:mm:ss)").grid(row=0, column=7, sticky=tk.W, padx=5, pady=5)
        self.duration_var = tk.StringVar(value="01:00:00")
        duration_entry = ttk.Entry(input_frame, textvariable=self.duration_var, width=10)
        duration_entry.grid(row=0, column=8, padx=5, pady=5)
        
        # Second row
        ttk.Label(input_frame, text="Streaming Key").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.streaming_key_var = tk.StringVar()
        streaming_key_entry = ttk.Entry(input_frame, textvariable=self.streaming_key_var, width=50)
        streaming_key_entry.grid(row=1, column=1, columnspan=6, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Add button
        add_btn = ttk.Button(input_frame, text="Tambah", command=self.add_stream)
        add_btn.grid(row=1, column=8, padx=5, pady=5)
        
        # Load existing streams into the table
        self.refresh_table()
        
        # Start checking for streams to start
        self.check_stream_thread = threading.Thread(target=self.check_streams, daemon=True)
        self.check_stream_thread.start()
        
    def browse_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*"))
        )
        if file_path:
            self.video_path_var.set(file_path)
    
    def add_stream(self):
        video_path = self.video_path_var.get()
        jam_mulai = f"{self.hour_var.get()}:{self.minute_var.get()}"
        streaming_key = self.streaming_key_var.get()
        durasi = self.duration_var.get()
        
        # Validation
        if not video_path:
            messagebox.showerror("Error", "Please select a video file")
            return
        
        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file does not exist")
            return
        
        if not streaming_key:
            messagebox.showerror("Error", "Please enter a streaming key")
            return
        
        # Add to the streams list
        stream_id = len(self.streams) + 1
        stream = {
            "id": stream_id,
            "video": os.path.basename(video_path),
            "video_path": video_path,
            "durasi": durasi,
            "jam_mulai": jam_mulai,
            "streaming_key": streaming_key,
            "status": "Menunggu"  # Waiting
        }
        
        self.streams.append(stream)
        self.save_streams()
        self.refresh_table()
        
        # Reset input fields
        self.video_path_var.set("")
        self.streaming_key_var.set("")
    
    def refresh_table(self):
        # Clear the table
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Populate with current streams
        for i, stream in enumerate(self.streams, 1):
            self.tree.insert("", "end", values=(
                i,
                stream["video"],
                stream["durasi"],
                stream["jam_mulai"],
                stream["streaming_key"],
                stream["status"],
                "-"
            ))
    
    def check_streams(self):
        """Check if any streams need to be started based on the schedule"""
        while True:
            current_time = datetime.datetime.now()
            current_time_str = f"{current_time.hour:02d}:{current_time.minute:02d}"
            
            for stream in self.streams:
                stream_id = stream["id"]
                if stream["jam_mulai"] == current_time_str and stream["status"] == "Menunggu":
                    # Start the stream
                    stream["status"] = "Sedang Live"
                    self.save_streams()
                    
                    # Start the streaming in a separate thread
                    stream_thread = threading.Thread(
                        target=self.start_stream,
                        args=(stream,),
                        daemon=True
                    )
                    self.stream_threads[stream_id] = stream_thread
                    stream_thread.start()
                    
                    # Update the table
                    self.refresh_table()
            
            # Check every 10 seconds
            time.sleep(10)
    
    def start_stream(self, stream):
        """Start the RTMP stream to YouTube"""
        video_path = stream["video_path"]
        streaming_key = stream["streaming_key"]
        
        # This is where you would implement the actual RTMP streaming
        # For example, using ffmpeg to stream the video to YouTube
        # Example ffmpeg command (not executed in this demo):
        # ffmpeg -re -i {video_path} -c:v libx264 -preset veryfast -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -c:a aac -b:a 160k -ac 2 -ar 44100 -f flv rtmp://a.rtmp.youtube.com/live2/{streaming_key}
        
        # For demo purposes, we'll just simulate streaming
        print(f"Started streaming {video_path} with key {streaming_key}")
        
        # Parse duration
        h, m, s = map(int, stream["durasi"].split(':'))
        duration_seconds = h * 3600 + m * 60 + s
        
        # Simulate streaming for the specified duration
        time.sleep(duration_seconds)
        
        # Update status when done
        for s in self.streams:
            if s["id"] == stream["id"]:
                s["status"] = "Selesai"  # Completed
        
        self.save_streams()
        self.refresh_table()
    
    def save_streams(self):
        """Save streams to a file"""
        try:
            with open("streams.json", "w") as f:
                json.dump(self.streams, f)
        except Exception as e:
            print(f"Error saving streams: {e}")
    
    def load_streams(self):
        """Load streams from a file"""
        try:
            if os.path.exists("streams.json"):
                with open("streams.json", "r") as f:
                    self.streams = json.load(f)
        except Exception as e:
            print(f"Error loading streams: {e}")
            self.streams = []

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamingScheduler(root)
    root.mainloop()