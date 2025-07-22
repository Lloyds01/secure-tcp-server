"""Threaded TCP Server with SSL support for exact string matching in files."""
from configparser import ConfigParser
import logging
import socket
import ssl
import threading
import time

logging.basicConfig(
    level=logging.DEBUG, format="DEBUG: %(asctime)s - %(message)s"
)  # Logs all messages to the console


class ThreadedServer:
    """Handles concurrent string search requests with SSL support."""

    def __init__(self, host="0.0.0.0", port=44445, test_mode=False):
        """Initialize the server with configuration.

        Args:
            host: IP address to bind to. Defaults to all interfaces.
            port: Port to listen on. Defaults to 44445.
            test_mode: Whether to use test_config.ini instead of config.ini.
        """
        self.host = host
        self.port = port
        self.test_mode = test_mode
        self._load_config()
        self.ssl_context = self._create_ssl_context()

    def _load_config(self):
        """Load configuration from config.ini or test_config.ini."""
        config_file = "test_config.ini" if self.test_mode else "config.ini"
        self.config = ConfigParser()
        try:
            read_files = self.config.read(config_file)
            if not read_files:
                logging.error(f"Config file '{config_file}' not found or is empty.")
            else:
                logging.info(f"Config file '{config_file}' loaded successfully.")
            self.file_path = self.config.get("DEFAULT", "linuxpath")
            self.reread = self.config.getboolean("DEFAULT", "reread_on_query")
            self.cached_lines = None
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {e}")
            raise
        except PermissionError as e:
            logging.error(f"Permission denied when reading config file: {e}")
            raise
        except Exception as e:
            logging.error(f"Failed to load config file '{config_file}': {e}")
            raise

    def process_query(self, query: str) -> str:
        """Process the client query and return a string response."""
        if self.search_string(query):
            return "STRING EXISTS\n"
        else:
            return "STRING NOT FOUND\n"

    def search_string(self, query: str) -> bool:
        """Search for an exact string match in the file.

        Args:
            query: String to search for.

        Returns:
            bool: True if an exact match is found, False otherwise.
        """
        start_time = time.time()
        try:
            if self.reread:
                with open(self.file_path, "r") as f:
                    result = any(line.strip() == query for line in f)
            else:
                if not self.cached_lines:
                    with open(self.file_path, "r") as f:
                        self.cached_lines = {line.strip() for line in f}
                result = query in self.cached_lines

            logging.debug(
                f"Query: '{query}' | "
                f"Time: {(time.time() - start_time)*1000:.2f}ms | "
                f"REREAD: {self.reread}"
            )
            return result

        except FileNotFoundError:
            logging.error(f"File not found: {self.file_path}")
            return False

    def handle_client(self, conn, addr):
        """Handle client connections with dynamic SSL support and payload size check."""
        MAX_PAYLOAD_SIZE = 1024
        try:
            with conn:
                try:
                    peek_data = conn.recv(1, socket.MSG_PEEK)
                    if not peek_data:
                        logging.debug(f"Client {addr} disconnected immediately.")
                        return
                except (ConnectionResetError, ssl.SSLError) as e:
                    logging.debug(f"Connection error from {addr} during peek: {e}")
                    return

                # Handle SSL handshake
                if self.ssl_context and self.config.getboolean(
                    "DEFAULT", "ssl_enabled"
                ):
                    try:
                        conn = self.ssl_context.wrap_socket(conn, server_side=True)
                        logging.debug(f"SSL handshake completed with {addr}.")
                    except ssl.SSLError as e:
                        if "UNEXPECTED_MESSAGE" in str(e):
                            if not self.config.getboolean("DEFAULT", "ssl_enabled"):
                                logging.debug(f"Non-SSL connected to SSL port {addr}.")
                            else:
                                logging.warning(
                                    f"Rejecting non-SSL connection (SSL required) "
                                    f"from {addr}."
                                )
                                conn.sendall(b"ERROR: SSL required\n")
                                return
                        else:
                            logging.error(f"SSL error with {addr}: {e}")
                            return

                # Read data from client
                data = conn.recv(MAX_PAYLOAD_SIZE + 1)  # +1 to detect overflow
                if not data:
                    logging.debug(f"Client {addr} disconnected.")
                    return

                if len(data) > MAX_PAYLOAD_SIZE:
                    logging.warning(
                        f"Payload too large from {addr} (>{MAX_PAYLOAD_SIZE} bytes)."
                    )
                    conn.sendall(b"ERROR: Payload too large. Max 1024 bytes allowed.\n")
                    return

                response = self.process_query(data.decode().strip())
                conn.sendall(response.encode())

        except (ConnectionResetError, BrokenPipeError) as e:
            logging.warning(f"Client {addr} disconnected: {e}")
        except Exception as e:
            logging.error(f"Error handling client {addr}: {e}")

    def _create_ssl_context(self):
        """Create SSL context if enabled in the config.

        Returns:
            Configured SSLContext or None if SSL is disabled.
        """
        if self.config.getboolean("DEFAULT", "ssl_enabled"):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain("cert.pem", "key.pem")
            return context
        return None

    def start(self):
        """Start the server in SSL or non-SSL mode based on the config."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen()

            if self.config.getboolean("DEFAULT", "ssl_enabled"):
                print(f"SSL server started on port {self.port}")
            else:
                print(f"Non-SSL server started on port {self.port}")

            try:
                while True:
                    conn, addr = sock.accept()
                    threading.Thread(
                        target=self.handle_client, args=(conn, addr), daemon=True
                    ).start()
            except KeyboardInterrupt:
                print("\nServer shutdown: Success.")


if __name__ == "__main__":
    server = ThreadedServer()
    server.start()
