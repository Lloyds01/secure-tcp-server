"""Unit tests for the search_string method in ThreadedServer."""

import tempfile

from server import ThreadedServer


def test_search_string_reread_enabled():
    """Test string search in reread mode (fresh file read each time)."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("hello\nworld\nfoo")
        f.flush()

        server = ThreadedServer(test_mode=True)
        server.file_path = f.name
        server.reread = True

        assert server.search_string("world") is True
        assert server.search_string("missing") is False


def test_search_string_with_cache():
    """Test string search with caching enabled (file read once)."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("apple\nbanana\ncarrot")
        f.flush()

        server = ThreadedServer(test_mode=True)
        server.file_path = f.name
        server.reread = False
        server.cached_lines = None

        assert server.search_string("banana") is True
        assert server.search_string("grape") is False
