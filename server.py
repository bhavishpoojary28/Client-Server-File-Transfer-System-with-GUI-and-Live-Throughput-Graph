import socket
import os
import time

HOST = '0.0.0.0'   
PORT = 5001
        

BUFFER_SIZE = 4096

def receive_file(conn):
  
    header = conn.recv(1024).decode()
    
    try:
        filename, filesize = header.split('|')
        filesize = int(filesize)
    except ValueError:
        print("Invalid header received:", header)
        return

    print(f"[+] Receiving file: {filename} ({filesize} bytes)")
    base_name = os.path.basename(filename)
    save_name = "RECEIVED_" + base_name

    bytes_received = 0
    start_time = time.time()

    with open(save_name, 'wb') as f:
        while bytes_received < filesize:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)
            bytes_received += len(data)

    end_time = time.time()
    total_time = end_time - start_time if end_time > start_time else 0.000001
    speed = bytes_received / total_time / (1024 * 1024)  # MB/s

    print(f"[+] File saved as: {save_name}")
    print(f"[+] Total received: {bytes_received} bytes")
    print(f"[+] Time taken: {total_time:.2f} seconds")
    print(f"[+] Average speed: {speed:.2f} MB/s")


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[+] Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            print(f"[+] Connection from {addr}")
            with conn:
                receive_file(conn)
            print("[+] Transfer complete. Waiting for next connection...\n")


if __name__ == "__main__":
    start_server()
