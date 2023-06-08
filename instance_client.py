import socket
import sys

def main():
    host = "127.0.0.1"
    port = int(sys.argv[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    token = b"A" * 128 + b"\0" * 2
    s.send(token)

    message = input("msg?: ")

    while True:
        s.send(message.encode("ascii"))
        data = s.recv(1024)
        print("Received from the server :", str(data.decode("ascii")))

        ans = input("\nDo you want to continue(y/n) :")
        if ans == "y":
            continue
        else:
            break
    s.close()


if __name__ == "__main__":
    main()
