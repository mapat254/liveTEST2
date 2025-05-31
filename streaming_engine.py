import subprocess
import logging
import os
import threading
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='streaming.log'
)
logger = logging.getLogger('streaming_engine')

class RTMPStreamer:
    """
    Handles the actual RTMP streaming to YouTube using ffmpeg
    """
    def __init__(self):
        self.active_streams = {}
        self.check_ffmpeg()
        
    def check_ffmpeg(self):
        """Check if ffmpeg is available on the system"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   check=False)
            if result.returncode != 0:
                logger.error("ffmpeg is not installed or not in PATH")
                raise RuntimeError("ffmpeg is not installed or not in PATH")
            else:
                logger.info("ffmpeg found, version: " + result.stdout.split('\n')[0])
        except FileNotFoundError:
            logger.error("ffmpeg is not installed or not in PATH")
            raise RuntimeError("ffmpeg is not installed or not in PATH")
    
    def start_stream(self, stream_id, video_path, streaming_key, duration, on_complete=None):
        """
        Start streaming a video file to YouTube using RTMP protocol
        
        Args:
            stream_id: Unique identifier for the stream
            video_path: Path to the video file
            streaming_key: YouTube RTMP streaming key
            duration: Duration in seconds
            on_complete: Callback function to execute when streaming completes
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        # Check if we already have this stream running
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} is already active")
            return False
        
        # Start stream in a separate thread
        thread = threading.Thread(
            target=self._stream_thread,
            args=(stream_id, video_path, streaming_key, duration, on_complete),
            daemon=True
        )
        self.active_streams[stream_id] = {
            'thread': thread,
            'start_time': datetime.now(),
            'status': 'initializing',
            'process': None,
            'connection_verified': False
        }
        thread.start()
        return True
    
    def _stream_thread(self, stream_id, video_path, streaming_key, duration, on_complete):
        """Thread function that handles the actual streaming process"""
        logger.info(f"Starting stream {stream_id} with video {video_path}")
        
        try:
            # RTMP URL for YouTube
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{streaming_key}"
            
            # Prepare ffmpeg command with detailed logging
            command = [
                'ffmpeg',
                '-re',  # Read input at native frame rate
                '-i', video_path,
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-maxrate', '3000k',
                '-bufsize', '6000k',
                '-pix_fmt', 'yuv420p',
                '-g', '50',
                '-c:a', 'aac',
                '-b:a', '160k',
                '-ac', '2',
                '-ar', '44100',
                '-f', 'flv',
                '-loglevel', 'info',  # Enable detailed logging
                rtmp_url
            ]
            
            logger.info(f"Starting ffmpeg stream: {' '.join(command)}")
            
            # Start the ffmpeg process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Store process reference
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['process'] = process
            
            # Monitor the process
            start_time = time.time()
            connection_attempts = 0
            max_connection_attempts = 30  # 30 seconds to establish connection
            
            while process.poll() is None:
                # Check if we've reached the duration
                if time.time() - start_time >= duration:
                    logger.info(f"Stream {stream_id} reached duration limit")
                    break
                
                # Check if stream was cancelled
                if stream_id not in self.active_streams:
                    logger.info(f"Stream {stream_id} was cancelled")
                    break
                
                # Read process output
                stderr_line = process.stderr.readline()
                if stderr_line:
                    line = stderr_line.strip()
                    logger.debug(f"ffmpeg output: {line}")
                    
                    # Check for successful connection
                    if "Speed:" in line or "frame=" in line:
                        if stream_id in self.active_streams and not self.active_streams[stream_id]['connection_verified']:
                            logger.info(f"Stream {stream_id} successfully connected to YouTube")
                            self.active_streams[stream_id]['connection_verified'] = True
                            self.active_streams[stream_id]['status'] = 'streaming'
                    
                    # Check for connection errors
                    if "Connection refused" in line or "Failed to connect" in line:
                        logger.error(f"Stream {stream_id} connection failed: {line}")
                        self.active_streams[stream_id]['status'] = 'error'
                        break
                
                # Check connection status during initialization
                if not self.active_streams[stream_id]['connection_verified']:
                    connection_attempts += 1
                    if connection_attempts >= max_connection_attempts:
                        logger.error(f"Stream {stream_id} failed to establish connection after {max_connection_attempts} seconds")
                        self.active_streams[stream_id]['status'] = 'error'
                        break
                    self.active_streams[stream_id]['status'] = 'connecting'
                
                time.sleep(1)
            
            # Check final process status
            if process.poll() is not None and process.returncode != 0:
                logger.error(f"Stream {stream_id} failed with return code {process.returncode}")
                stderr_output = process.stderr.read()
                if stderr_output:
                    logger.error(f"ffmpeg error output: {stderr_output}")
                self.active_streams[stream_id]['status'] = 'error'
            
        except Exception as e:
            logger.error(f"Error in stream thread: {str(e)}")
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'error'
            raise
        
        finally:
            # Clean up
            if stream_id in self.active_streams:
                process = self.active_streams[stream_id].get('process')
                if process and process.poll() is None:
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except:
                        process.kill()
                        process.wait()
                
                if self.active_streams[stream_id]['status'] not in ['error']:
                    self.active_streams[stream_id]['status'] = 'completed'
                del self.active_streams[stream_id]
            
            # Call completion callback
            if on_complete:
                on_complete(stream_id)
    
    def stop_stream(self, stream_id):
        """Stop an active stream"""
        if stream_id in self.active_streams:
            logger.info(f"Stopping stream {stream_id}")
            
            # Get process reference
            stream_data = self.active_streams[stream_id]
            process = stream_data.get('process')
            
            # Terminate process if it exists and is running
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # Remove from active streams
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