import subprocess
import sys
import os

def check_python_version():
    if sys.version_info < (3, 6):
        print("Python 3.6 or higher is required")
        sys.exit(1)

def install_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
        print("ffmpeg is already installed")
    except:
        print("Installing ffmpeg...")
        if sys.platform == "win32":
            print("Please install ffmpeg manually from https://ffmpeg.org/download.html")
            print("Make sure to add it to your system PATH")
        elif sys.platform == "darwin":
            subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
        else:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)

def install_python_dependencies():
    print("Installing Python dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)

def main():
    print("Setting up YouTube RTMP Scheduler...")
    check_python_version()
    install_ffmpeg()
    install_python_dependencies()
    print("\nSetup completed successfully!")
    print("You can now run the application using: python main.py")

if __name__ == "__main__":
    main()