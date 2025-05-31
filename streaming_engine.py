import subprocess
import logging
import os
import threading
import time
from datetime import datetime
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='streaming.log'
)
logger = logging.getLogger('streaming_engine')

class RTMPStreamer:
    def __init__(self):
        self.active_streams = {}
        self.ffmpeg_available = self.check_ffmpeg()
        
    def check_ffmpeg(self):
        """Check if ffmpeg is available and return True if it is"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   check=True)
            logger.info("FFmpeg found, version: " + result.stdout.split('\n')[0])
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"FFmpeg check failed: {str(e)}")
            return False
    
    def start_stream(self, stream_id, video_path, streaming_key, duration, on_complete=None):
        """Start streaming a video file to YouTube using RTMP protocol"""
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} is already active")
            return False
        
        if not self.ffmpeg_available:
            logger.error("FFmpeg is not available. Cannot start actual streaming.")
            return False
        
        thread = threading.Thread(
            target=self._stream_thread,
            args=(stream_id, video_path, streaming_key, duration, on_complete),
            daemon=True
        )
        
        self.active_streams[stream_id] = {
            'thread': thread,
            'start_time': datetime.now(),
            'status': 'initializing',
            'process': None
        }
        
        thread.start()
        return True
    
    def _stream_thread(self, stream_id, video_path, streaming_key, duration, on_complete):
        """Thread function that handles the actual streaming process"""
        logger.info(f"Starting stream {stream_id} with video {video_path}")
        
        try:
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{streaming_key}"
            
            # FFmpeg command with improved streaming parameters
            command = [
                'ffmpeg',
                '-re',  # Read input at native frame rate
                '-i', video_path,
                '-c:v', 'libx264',  # Video codec
                '-preset', 'veryfast',  # Encoding preset
                '-tune', 'zerolatency',  # Tune for streaming
                '-maxrate', '4500k',  # Maximum bitrate
                '-bufsize', '9000k',  # Buffer size (2x maxrate)
                '-pix_fmt', 'yuv420p',  # Pixel format
                '-g', '60',  # Keyframe interval
                '-c:a', 'aac',  # Audio codec
                '-b:a', '160k',  # Audio bitrate
                '-ac', '2',  # Audio channels
                '-ar', '44100',  # Audio sample rate
                '-f', 'flv',  # Output format
                '-flvflags', 'no_duration_filesize',  # Important for live streaming
                rtmp_url
            ]
            
            # Update status to streaming
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'connecting'
            
            # Start FFmpeg process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['process'] = process
                self.active_streams[stream_id]['status'] = 'streaming'
            
            # Monitor the process
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time >= duration:
                    # Gracefully stop the stream
                    self.stop_stream(stream_id)
                    break
                time.sleep(1)
            
            # Check process return code
            if process.returncode == 0:
                logger.info(f"Stream {stream_id} completed successfully")
                if stream_id in self.active_streams:
                    self.active_streams[stream_id]['status'] = 'completed'
            else:
                logger.error(f"Stream {stream_id} failed with return code {process.returncode}")
                if stream_id in self.active_streams:
                    self.active_streams[stream_id]['status'] = 'error'
            
        except Exception as e:
            logger.error(f"Error in stream thread: {str(e)}")
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'error'
        
        finally:
            # Cleanup
            if stream_id in self.active_streams:
                process = self.active_streams[stream_id].get('process')
                if process and process.poll() is None:
                    try:
                        os.kill(process.pid, signal.SIGTERM)
                        process.wait(timeout=5)
                    except:
                        try:
                            os.kill(process.pid, signal.SIGKILL)
                        except:
                            pass
                
                del self.active_streams[stream_id]
            
            if on_complete:
                on_complete(stream_id)
    
    def stop_stream(self, stream_id):
        """Stop an active stream"""
        if stream_id in self.active_streams:
            logger.info(f"Stopping stream {stream_id}")
            stream_data = self.active_streams[stream_id]
            process = stream_data.get('process')
            
            if process and process.poll() is None:
                try:
                    # Try graceful termination first
                    os.kill(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except:
                    try:
                        # Force kill if graceful termination fails
                        os.kill(process.pid, signal.SIGKILL)
                    except:
                        pass
            
            del self.active_streams[stream_id]
            return True
        return False
    
    def get_stream_status(self, stream_id):
        """Get the status of a stream"""
        if stream_id in self.active_streams:
            return self.active_streams[stream_id]['status']
        return None
    
    def get_active_streams(self):
        """Get all active streams"""
        return {k: v['status'] for k, v in self.active_streams.items()}
