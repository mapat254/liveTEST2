# YouTube RTMP Live Streaming Scheduler

A Python application for scheduling and managing YouTube RTMP live streams.

## Features

- Schedule videos for streaming to YouTube via RTMP
- Manage multiple scheduled streams with start times
- Track currently live streams
- Set custom duration for each stream
- Easy-to-use graphical interface
- Automatic stream management

## Requirements

- Python 3.6 or higher
- Tkinter (included with most Python installations)
- ffmpeg (optional, for actual streaming functionality)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Install ffmpeg if you want actual streaming functionality:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - macOS: `brew install ffmpeg`
   - Linux: `apt install ffmpeg` or equivalent for your distribution

## Usage

1. Run the application:

```bash
python main.py
```

2. The application window will open.
3. To schedule a new stream:
   - Click "Pilih Video" to select your video file
   - Set the start time using the hour and minute dropdowns
   - Enter your YouTube RTMP streaming key
   - Set the duration in hh:mm:ss format
   - Click "Tambah" to add the stream to the schedule

4. The application will automatically start streams at their scheduled times.

## Note on YouTube Streaming

To stream to YouTube, you need:
1. A YouTube account with live streaming enabled
2. A stream key from YouTube Studio
3. A video file to stream

## License

This project is licensed under the MIT License - see the LICENSE file for details.