import socket


def auth(client_socket: socket.socket) -> tuple[bytes | None, bool]:
    """
    Takes in a newly connected client socket, and checks if it is authenticated via a token.
    If the token is valid, return the token for the instancer to use as an identifier.
    Else, return None.
    Also, return an additional attribute denoting whether the instancer should reset all instances associated with the token.
    """
    correct_token = b"A" * 128
    reset_id = b"\x00" * 2
    reset = False
    try:
        token = client_socket.recv(128 + 2)  # last 2 bytes are the id
        if token[:128] == correct_token:
            if token.endswith(reset_id):
                reset = True
            return (token, reset)
    except Exception as e:
        print(e)
        pass
    return (None, False)


def tokens_associated(token: bytes | str, token2: bytes | str) -> bool:
    """
    Returns a boolean based on whether the two input tokens are associated.
    """
    if len(token) < 128 or len(token2) < 128:
        return False

    if token[:128] == token2[:128]:
        return True

    return False
