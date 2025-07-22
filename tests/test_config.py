"""Unit tests for configuration loading in the ThreadedServer."""

import os

from server import ThreadedServer


def test_config_loading(tmp_path):
    """
    Test that ThreadedServer loads configuration correctly from test_config.ini.

    Verifies that file path and reread flag are set according to the configuration.
    """
    test_config_path = tmp_path / "test_config.ini"
    test_config_path.write_text(
        """[DEFAULT]
        linuxpath=dummy.txt
        reread_on_query=False
        ssl_enabled=False"""
    )

    os.chdir(tmp_path)
    server = ThreadedServer(test_mode=True)

    assert server.file_path == "dummy.txt"
    assert server.reread is False
