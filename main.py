import tkinter as tk
from stream_scheduler import StreamingScheduler

def main():
    root = tk.Tk()
    app = StreamingScheduler(root)
    root.mainloop()

if __name__ == "__main__":
    main()