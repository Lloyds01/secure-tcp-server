"""TCP client implementation for server communication."""
from configparser import ConfigParser
import socket
import ssl
import sys


def send_query(query, host="127.0.0.1", port=44445):
    """Send a query to the server to check if a string exists in its file.

    Uses SSL/TLS or plain TCP based on config.ini settings.

    Args:
        query (str): The string to search for.
        host (str): Server IP or hostname. Default is '127.0.0.1'.
        port (int): Server port. Default is 44445.

    Returns:
        str: The server response.
    """
    config = ConfigParser()
    config.read("config.ini")
    use_ssl = config.getboolean("DEFAULT", "ssl_enabled")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as sock:
        if use_ssl:
            sock = context.wrap_socket(sock, server_hostname=host)
            print("SSL connection established.")
        else:
            print("Non-SSL connection established.")

        sock.sendall(query.encode())
        response = sock.recv(1024).decode()
        print(response)
        return response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        send_query(sys.argv[1])
    else:
        print("Usage: python client.py '<query_string>'")
