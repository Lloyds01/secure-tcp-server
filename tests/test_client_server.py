"""Test suite for client-server interaction using the ThreadedServer class."""

import socket
import threading
import time

from server import ThreadedServer


def test_handle_client_response_found():
    """
    Test server's response when the requested string is found.

    Simulates a client sending a string that exists in the data source,
    and verifies the server responds with 'STRING EXISTS'.
    """
    server = ThreadedServer(test_mode=True)
    server.search_string = lambda x: True

    parent_sock, child_sock = socket.socketpair()

    def client_sender():
        time.sleep(0.1)
        child_sock.sendall(b"apple\n")
        data = child_sock.recv(1024)
        assert data == b"STRING EXISTS\n"
        child_sock.close()

    t = threading.Thread(target=client_sender)
    t.start()

    server.handle_client(parent_sock, ("127.0.0.1", 12345))
    parent_sock.close()
    t.join()


def test_handle_client_response_not_found():
    """
    Test server's response when the requested string is not found.

    Simulates a client sending a string that does not exist in the data source,
    and verifies the server responds with 'STRING NOT FOUND'.
    """
    server = ThreadedServer(test_mode=True)
    server.search_string = lambda x: False

    parent_sock, child_sock = socket.socketpair()

    def client_sender():
        time.sleep(0.1)
        child_sock.sendall(b"banana\n")
        data = child_sock.recv(1024)
        assert data == b"STRING NOT FOUND\n"
        child_sock.close()

    t = threading.Thread(target=client_sender)
    t.start()

    server.handle_client(parent_sock, ("127.0.0.1", 12345))
    parent_sock.close()
    t.join()
