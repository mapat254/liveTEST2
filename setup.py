from setuptools import setup, find_packages

setup(
    name="youtube-rtmp-scheduler",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'python-tk>=3.6.0',
        'ffmpeg-python>=0.2.0',
        'pillow>=9.0.0',
        'python-dateutil>=2.8.2',
        'colorlog>=6.7.0',
        'watchdog>=2.1.9',
    ],
    python_requires='>=3.6',
)