import os
import pytest
import time
import requests
from pathlib import Path
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
import sys
import threading
import uvicorn
from contextlib import contextmanager
from sample_rest_api.app.main import app, create_category, read_category, update_category, delete_category, search_products

@pytest.fixture(scope="session")
def sample_api_port():
    return 9000

@pytest.fixture(scope="session")
def sample_api_url(sample_api_port):
    return f"http://localhost:{sample_api_port}"

class UvicornTestServer(uvicorn.Server):
    """Uvicorn test server

    Usage:
        @pytest.fixture
        def server():
            return UvicornTestServer()

        def test_server(server):
            with server.run_in_thread():
                # Test code here
                ...
    """
    def install_signal_handlers(self):
        # Disable signal handlers in test mode
        pass

    @contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(0.1)
            yield
        finally:
            self.should_exit = True
            thread.join()

@pytest.fixture(scope="session")
def sample_api_server(sample_api_port):
    # Configure uvicorn server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=sample_api_port,
        log_level="error"
    )
    server = UvicornTestServer(config=config)
    
    # Start server in a thread
    with server.run_in_thread():
        # Wait for the server to start
        max_retries = 30
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = requests.get(f"http://localhost:{sample_api_port}/docs")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.1)
            retry_count += 1
        else:
            raise Exception("Failed to start API server")
        
        yield server

@pytest.fixture
def mcp_client(sample_api_url, sample_api_server):
    """Create an MCP client for testing"""
    client = OpenAPIMCPServer(
        server_name="Sample API",
        openapi_spec=f"{sample_api_url}/openapi.json",
        server_url=sample_api_url
    )
    return client

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up the database after each test"""
    yield
    # Database is in-memory, so it's automatically cleaned up
    pass
