"""Integration tests for the ThreadedServer application."""
from configparser import ConfigParser
from contextlib import contextmanager
import os
import socket
import ssl
import subprocess
import tempfile
import threading
import time

from client import send_query
import pytest
from server import ThreadedServer


TEST_QUERY_PRESENT = "MATCH_ME"
TEST_QUERY_ABSENT = "DOES_NOT_EXIST"
TEST_CONFIG_FILE = "test_config.ini"


def generate_ssl_certificates(cert_file, key_file):
    """Generate a self-signed SSL certificate for test use."""
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-nodes",
            "-days",
            "1",
            "-newkey",
            "rsa:2048",
            "-keyout",
            key_file,
            "-out",
            cert_file,
            "-subj",
            "/CN=localhost",
        ],
        check=True,
    )


def write_test_file():
    """Create a temporary file containing a known query string."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "test_file.txt")
    with open(file_path, "w") as f:
        f.write(TEST_QUERY_PRESENT + "\n")
    return file_path


def update_test_config(file_path, ssl_enabled=True):
    """Write a test config to test_config.ini with the given file path and SSL flag."""
    config = ConfigParser()
    config["DEFAULT"] = {
        "linuxpath": file_path,
        "reread_on_query": "True",
        "ssl_enabled": str(ssl_enabled),
    }
    with open(TEST_CONFIG_FILE, "w") as f:
        config.write(f)


@contextmanager
def run_server_in_thread(
    ssl_enabled=False, certfile=None, keyfile=None, host="localhost", port=44445
):
    """Run the server in a background thread with optional SSL."""
    server = ThreadedServer(host=host, port=port)

    if ssl_enabled:
        server.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server.ssl_context.load_cert_chain(certfile, keyfile)

    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()

    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                break
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(0.1)
    else:
        raise TimeoutError("Server failed to start")

    try:
        yield
    finally:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                pass  # Trigger accept()
        except Exception:
            pass
        server_thread.join(timeout=1)


def create_test_certs(cert_path, key_path):
    """Generate temporary self-signed certificates using cryptography."""
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
        )
        .sign(key, hashes.SHA256())
    )

    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def test_concurrent_connections():
    """Verify that the server handles multiple simultaneous client queries."""
    file_path = write_test_file()
    update_test_config(file_path, ssl_enabled=False)
    run_server_in_thread()

    results = []

    def worker(query):
        res = send_query(query)
        results.append(res)

    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker, args=(TEST_QUERY_PRESENT,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for res in results:
        assert "STRING EXISTS" in res


def test_test_config_isolation():
    """Ensure test config file is isolated and correctly written."""
    file_path = write_test_file()
    update_test_config(file_path, ssl_enabled=False)
    run_server_in_thread()

    assert os.path.exists(TEST_CONFIG_FILE)
    with open(TEST_CONFIG_FILE, "r") as f:
        contents = f.read()
    assert "linuxpath" in contents
    assert "ssl_enabled" in contents


def test_empty_query(caplog):
    """Verify behavior when an empty query is sent."""
    server = ThreadedServer(test_mode=True)
    server.cached_lines = {"hello", "world"}
    caplog.set_level("DEBUG")

    response = server.process_query("")
    assert response == "STRING NOT FOUND\n"
    assert "Query: ''" in caplog.text


def test_empty_file(tmp_path):
    """Check behavior when the source file is empty."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    server = ThreadedServer(test_mode=True)
    server.file_path = str(file_path)
    server.reread = True

    assert not server.search_string("query")


def test_search_cache_mode(tmp_path):
    """Test cached search mode when reread is disabled."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("cached_string\n")

    server = ThreadedServer(test_mode=True)
    server.cached_lines = {"cached_string"}
    server.reread = False
    server.file_path = str(file_path)

    assert server.search_string("cached_string")
    assert not server.search_string("missing_string")


def test_file_read_failure():
    """Test search behavior when the file does not exist."""
    server = ThreadedServer(test_mode=True)
    server.file_path = "nonexistent_file.txt"
    server.reread = True

    result = server.search_string("anything")
    assert result is False


def test_invalid_config_raises():
    """Test that invalid configuration leads to failure."""
    server = ThreadedServer(test_mode=True)

    # Simulate invalid config by omitting necessary fields
    server.host = None  # or some invalid value
    server.port = "not-a-port"  # intentionally invalid
    with pytest.raises(Exception):
        server.start()


def test_generate_ssl_certificates(tmp_path):
    """Test that SSL certificates are generated using subprocess."""
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    generate_ssl_certificates(str(cert_path), str(key_path))

    assert cert_path.exists()
    assert key_path.exists()
    assert "BEGIN CERTIFICATE" in cert_path.read_text()


def test_create_test_certs(tmp_path):
    """Test that self-signed certificates are created using cryptography."""
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"

    create_test_certs(cert_path, key_path)

    assert cert_path.exists()
    assert key_path.exists()
    assert "BEGIN CERTIFICATE" in cert_path.read_text()
    assert "PRIVATE KEY" in key_path.read_text()


if __name__ == "__main__":
    test_concurrent_connections()
    test_test_config_isolation()
    test_empty_query()
    test_empty_file()
    test_search_cache_mode()
    test_file_read_failure()
    test_invalid_config_raises()
    test_generate_ssl_certificates()
    test_create_test_certs()
    print("✅ All integration tests passed.")
