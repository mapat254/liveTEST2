import subprocess
import sys
import os
import platform

def check_python_version():
    if sys.version_info < (3, 6):
        print("Python 3.6 or higher is required")
        sys.exit(1)

def install_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
        print("✓ ffmpeg is already installed")
        return True
    except:
        print("Installing ffmpeg...")
        system = platform.system().lower()
        
        if system == "windows":
            print("""
Please install FFmpeg manually:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the archive
3. Add the bin folder to your system PATH
4. Restart your terminal/IDE
""")
            return False
        elif system == "darwin":
            try:
                # Check if Homebrew is installed
                subprocess.run(['brew', '--version'], check=True, capture_output=True)
            except:
                print("Installing Homebrew first...")
                subprocess.run(['/bin/bash', '-c', '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'], check=True)
            
            subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
            return True
        else:  # Linux
            try:
                subprocess.run(['sudo', 'apt-get', 'update'], check=True)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
                return True
            except:
                try:
                    # Try with yum if apt-get fails
                    subprocess.run(['sudo', 'yum', 'install', '-y', 'ffmpeg'], check=True)
                    return True
                except:
                    print("Failed to install FFmpeg. Please install it manually for your distribution")
                    return False

def install_python_dependencies():
    print("Installing Python dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)

def main():
    print("Setting up YouTube RTMP Scheduler...")
    check_python_version()
    
    if not install_ffmpeg():
        print("\nWARNING: FFmpeg installation failed or requires manual installation.")
        print("The application will not be able to perform actual streaming without FFmpeg.")
        user_input = input("Do you want to continue with the setup anyway? (y/n): ")
        if user_input.lower() != 'y':
            sys.exit(1)
    
    install_python_dependencies()
    print("\nSetup completed!")
    print("You can now run the application using: streamlit run app.py")

if __name__ == "__main__":
    main()
