import socket
import multiprocessing
import subprocess
import sys
import time
import threading
from dataclasses import dataclass
from utils import stop_process, check_port_avail
from auth import auth, tokens_associated


@dataclass
class Instance:
    process: multiprocessing.Process
    client_socket: socket.socket
    port: int
    start_time: float
    token: bytes | str


instances: list[Instance] = []
available_ports = [x for x in range(8000, 8010)]
waiting_ports = []
HOST = ""
PORT = 12345
MAX_TIMEOUT = 20  # 20 seconds


def handle_connection(client_socket, port, use_existing_instance=False):
    if not use_existing_instance:
        # start_cmd = f"python3 sample_server/server.py {port}"  # TODO: drop privileges in running this! ie use setuid binary
        start_cmd = f"./start_cmd.sh {port}"  # TODO: drop privileges in running this! ie use setuid binary
        subprocess.Popen(start_cmd.split(" "), stdout=subprocess.DEVNULL)
        time.sleep(1)  # wait for server to start up

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(("127.0.0.1", port))

    def inward_proxy(client_socket, server_socket):
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            server_socket.send(data)

    def outward_proxy(client_socket, server_socket):
        while True:
            data = server_socket.recv(1024)
            if not data:
                break
            client_socket.send(data)

    data_in = threading.Thread(
        target=inward_proxy,
        args=(
            client_socket,
            server_socket,
        ),
        daemon=True,
    )
    data_out = threading.Thread(
        target=outward_proxy,
        args=(
            client_socket,
            server_socket,
        ),
    )
    data_in.start()
    data_out.start()
    data_out.join()
    data_in.join()


def prune_connection(client_socket, port):
    global available_ports
    global waiting_ports
    client_socket.close()
    stop_process(port)
    if check_port_avail(port):
        available_ports.insert(0, port)
    else:
        waiting_ports.insert(0, port)


lock = threading.Lock()


def handle_incoming_connections(proxy_server: socket.socket):
    global lock, instances, available_ports, waiting_ports
    while True:
        # accept one connection
        if len(available_ports) > 0:
            client_socket, addr = proxy_server.accept()
            token, reset = auth(client_socket)
            if token is None:
                client_socket.close()
                continue

            if reset:
                # reset all instances associated with the token
                with lock:
                    for instance in instances:
                        if tokens_associated(instance.token, token):
                            print(f"[~] Resetting instance {instance=}")
                            # TODO: make the following a function. Also, cleanup any remaining Docker containers.
                            instances.remove(instance)
                            instance.process.kill()
                            prune_connection(instance.client_socket, instance.port)

            with lock:
                existing_instance = False
                for instance in instances:
                    if instance.token == token:
                        existing_instance = True
                        server_port = instance.port
                        break
                else:
                    server_port = available_ports.pop()

                print(
                    f"[+] Accepted connection from {addr[0]}:{addr[1]} --> {server_port=}"
                )
                p = multiprocessing.Process(
                    target=handle_connection,
                    args=(client_socket, server_port, existing_instance),
                )

                if not existing_instance:
                    instances.append(
                        Instance(p, client_socket, server_port, time.time(), token)
                    )
                p.start()


def handle_ports():
    global lock, instances, available_ports, waiting_ports
    while True:
        # check waiting ports
        with lock:
            for port in waiting_ports:
                if check_port_avail(port):
                    print(f"[~] {port=} is now available")
                    waiting_ports.remove(port)
                    available_ports.insert(0, port)

        # prune timed out instances and dead processes
        with lock:
            now = time.time()
            for instance in instances:
                if (
                    not instance.process.is_alive()
                    or (now - instance.start_time) > MAX_TIMEOUT
                ):
                    if (now - instance.start_time) > MAX_TIMEOUT:
                        print(f"[-] Pruning timed out instance {instance=}")
                    else:
                        print(f"[-] Pruning dead instance {instance=}")
                    instances.remove(instance)
                    instance.process.kill()
                    prune_connection(instance.client_socket, instance.port)

        with lock:
            # prune oldest connections
            if len(available_ports) == 0 and len(waiting_ports) == 0:
                instance = instances[0]
                print(f"[-] Pruning oldest instance {instance=}")
                instances = instances[1:]
                instance.process.kill()
                prune_connection(instance.client_socket, instance.port)

        time.sleep(1)


def main():
    global instances, available_ports, waiting_ports
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((HOST, PORT))
    print(f"[+] Instancer bound to {PORT=}")

    proxy_server.listen(5)
    print("[+] Instancer listening")

    available_ports = list(set(available_ports))
    for port in available_ports:
        if not check_port_avail(port):
            available_ports.remove(port)
            waiting_ports.insert(0, port)
    print(f"[~] {available_ports=}")
    print(f"[~] {waiting_ports=}")

    t1 = threading.Thread(target=handle_incoming_connections, args=(proxy_server,))
    t2 = threading.Thread(target=handle_ports)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    proxy_server.close()


if __name__ == "__main__":
    try:
        PORT = int(sys.argv[1])
    except:
        print("Usage: python3 instancer.py {PORT}")
        quit()

    main()
