from psutil import process_iter
from signal import SIGTERM  # or SIGKILL


def stop_process(port):
    for proc in process_iter():
        for conns in proc.connections(kind="inet"):
            if conns.laddr.port == port:
                # print(conns)
                proc.send_signal(SIGTERM)  # or SIGKILL
                return True
    return False


import socket, errno

# https://superuser.com/questions/1627361/what-would-prevent-a-tcp-server-port-once-closed-from-being-re-opened-right-a
def check_port_avail(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free = True
    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            # print("Port is already in use")
            free = False
        else:
            # something else raised the socket.error exception
            # print(e)
            free = False

    s.close()
    return free


# stopped = stop_process(5555)
# free = check_port_avail(5555)
# stopped2 = stop_process(5555)
# print(f"stopped: {stopped}")
# print(f"free: {free}")
# print(f"time-wait: {free and not stopped2}")