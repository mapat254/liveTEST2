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
    def __init__(self):
        self.active_streams = {}
        try:
            self.check_ffmpeg()
        except RuntimeError as e:
            logger.warning(f"FFmpeg check failed: {str(e)}")
            # Continue without ffmpeg for UI testing
            pass
        
    def check_ffmpeg(self):
        """Check if ffmpeg is available on the system"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   check=False)
            if result.returncode != 0:
                logger.warning("ffmpeg is not installed or not in PATH")
            else:
                logger.info("ffmpeg found, version: " + result.stdout.split('\n')[0])
        except FileNotFoundError:
            logger.warning("ffmpeg is not installed or not in PATH")
    
    def start_stream(self, stream_id, video_path, streaming_key, duration, on_complete=None):
        """
        Start streaming a video file to YouTube using RTMP protocol
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} is already active")
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
            'process': None,
            'connection_verified': False
        }
        thread.start()
        return True
    
    def _stream_thread(self, stream_id, video_path, streaming_key, duration, on_complete):
        """Thread function that handles the actual streaming process"""
        logger.info(f"Starting stream {stream_id} with video {video_path}")
        
        try:
            # Simulate streaming for testing when ffmpeg is not available
            try:
                subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
                use_ffmpeg = True
            except:
                use_ffmpeg = False
                logger.warning("FFmpeg not available, running in simulation mode")
            
            if use_ffmpeg:
                rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{streaming_key}"
                command = [
                    'ffmpeg',
                    '-re',
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
                    rtmp_url
                ]
                
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
                
                process.wait()
                
                if process.returncode != 0:
                    logger.error(f"Stream {stream_id} failed with return code {process.returncode}")
                    self.active_streams[stream_id]['status'] = 'error'
            else:
                # Simulation mode
                self.active_streams[stream_id]['status'] = 'simulated'
                time.sleep(duration)  # Simulate streaming duration
                
        except Exception as e:
            logger.error(f"Error in stream thread: {str(e)}")
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['status'] = 'error'
        
        finally:
            if stream_id in self.active_streams:
                if self.active_streams[stream_id]['status'] not in ['error']:
                    self.active_streams[stream_id]['status'] = 'completed'
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
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
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
