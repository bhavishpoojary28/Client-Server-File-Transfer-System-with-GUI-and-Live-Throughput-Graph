import socket
import threading
import time
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt

BUFFER_SIZE = 4096

class FileTransferClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP File Transfer Monitor")

        # Variables
        self.server_ip_var = tk.StringVar(value="127.0.0.1")
        self.server_port_var = tk.IntVar(value=5001)
        self.file_path_var = tk.StringVar(value="No file selected")
        self.status_var = tk.StringVar(value="Idle")
        self.current_speed_var = tk.StringVar(value="0 MB/s")
        self.avg_speed_var = tk.StringVar(value="0 MB/s")
        self.elapsed_time_var = tk.StringVar(value="0 s")
        self.progress_var = tk.StringVar(value="0 / 0 MB")

        # For graph
        self.time_points = []
        self.speed_points = []

        self._build_ui()

    def _build_ui(self):
        # Server IP + Port
        frame_conn = tk.Frame(self.root, padx=10, pady=5)
        frame_conn.pack(fill="x")

        tk.Label(frame_conn, text="Server IP:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_conn, textvariable=self.server_ip_var, width=15).grid(row=0, column=1, padx=5)

        tk.Label(frame_conn, text="Port:").grid(row=0, column=2, sticky="w")
        tk.Entry(frame_conn, textvariable=self.server_port_var, width=7).grid(row=0, column=3, padx=5)

        # File selection
        frame_file = tk.Frame(self.root, padx=10, pady=5)
        frame_file.pack(fill="x")

        tk.Button(frame_file, text="Select File", command=self.select_file).grid(row=0, column=0)
        tk.Label(frame_file, textvariable=self.file_path_var, wraplength=400, anchor="w", justify="left").grid(row=0, column=1, padx=5)

        # Status & Metrics
        frame_stats = tk.Frame(self.root, padx=10, pady=5)
        frame_stats.pack(fill="x")

        tk.Label(frame_stats, text="Status:").grid(row=0, column=0, sticky="w")
        tk.Label(frame_stats, textvariable=self.status_var).grid(row=0, column=1, sticky="w")

        tk.Label(frame_stats, text="Current Speed:").grid(row=1, column=0, sticky="w")
        tk.Label(frame_stats, textvariable=self.current_speed_var).grid(row=1, column=1, sticky="w")

        tk.Label(frame_stats, text="Average Speed:").grid(row=2, column=0, sticky="w")
        tk.Label(frame_stats, textvariable=self.avg_speed_var).grid(row=2, column=1, sticky="w")

        tk.Label(frame_stats, text="Elapsed Time:").grid(row=3, column=0, sticky="w")
        tk.Label(frame_stats, textvariable=self.elapsed_time_var).grid(row=3, column=1, sticky="w")

        tk.Label(frame_stats, text="Progress:").grid(row=4, column=0, sticky="w")
        tk.Label(frame_stats, textvariable=self.progress_var).grid(row=4, column=1, sticky="w")

        # Buttons
        frame_btn = tk.Frame(self.root, padx=10, pady=10)
        frame_btn.pack()

        tk.Button(frame_btn, text="Start Transfer", command=self.start_transfer_thread).grid(row=0, column=0, padx=5)
        tk.Button(frame_btn, text="Show Speed Graph", command=self.show_graph).grid(row=0, column=1, padx=5)

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path_var.set(path)

    def start_transfer_thread(self):
        t = threading.Thread(target=self.start_transfer, daemon=True)
        t.start()

    def start_transfer(self):
        file_path = self.file_path_var.get()
        if not os.path.isfile(file_path):
            messagebox.showerror("Error", "Please select a valid file first.")
            return

        server_ip = self.server_ip_var.get()
        server_port = self.server_port_var.get()

        filesize = os.path.getsize(file_path)
        self.time_points = []
        self.speed_points = []

        self.status_var.set("Connecting...")
        self.current_speed_var.set("0 MB/s")
        self.avg_speed_var.set("0 MB/s")
        self.elapsed_time_var.set("0 s")
        self.progress_var.set(f"0 / {filesize / (1024*1024):.2f} MB")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_ip, server_port))
                self.status_var.set("Connected. Sending...")

                # Send header: filename|filesize
                header = f"{os.path.basename(file_path)}|{filesize}"
                s.sendall(header.encode())

                time.sleep(0.1)  # small delay to separate header and data

                bytes_sent = 0
                start_time = time.time()
                last_time = start_time
                last_bytes_sent = 0

                with open(file_path, "rb") as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        s.sendall(data)
                        bytes_sent += len(data)

                        now = time.time()
                        elapsed = now - start_time
                        interval = now - last_time

                        # Instant speed for this interval
                        if interval > 0:
                            inst_bytes = bytes_sent - last_bytes_sent
                            inst_speed = inst_bytes / interval / (1024 * 1024)  # MB/s
                            self.time_points.append(elapsed)
                            self.speed_points.append(inst_speed)

                            # Update GUI labels
                            self.current_speed_var.set(f"{inst_speed:.2f} MB/s")

                            avg_speed = bytes_sent / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                            self.avg_speed_var.set(f"{avg_speed:.2f} MB/s")
                            self.elapsed_time_var.set(f"{int(elapsed)} s")
                            self.progress_var.set(
                                f"{bytes_sent / (1024*1024):.2f} / {filesize / (1024*1024):.2f} MB"
                            )

                            last_time = now
                            last_bytes_sent = bytes_sent

                total_time = time.time() - start_time
                avg_speed = bytes_sent / (total_time * 1024 * 1024) if total_time > 0 else 0

                self.status_var.set("Transfer Complete")
                self.current_speed_var.set("0 MB/s")
                self.avg_speed_var.set(f"{avg_speed:.2f} MB/s")
                self.elapsed_time_var.set(f"{int(total_time)} s")
                self.progress_var.set(
                    f"{bytes_sent / (1024*1024):.2f} / {filesize / (1024*1024):.2f} MB"
                )

                messagebox.showinfo("Done", "File transfer completed successfully!")

        except Exception as e:
            self.status_var.set("Error")
            messagebox.showerror("Error", f"Transfer failed:\n{e}")

    def show_graph(self):
        if not self.time_points or not self.speed_points:
            messagebox.showinfo("Info", "No transfer data to display.")
            return

        plt.figure()
        plt.plot(self.time_points, self.speed_points, marker='o')
        plt.xlabel("Time (seconds)")
        plt.ylabel("Speed (MB/s)")
        plt.title("File Transfer Speed vs Time")
        plt.grid(True)
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferClientApp(root)
    root.mainloop()
