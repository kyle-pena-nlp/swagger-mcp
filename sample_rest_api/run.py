import uvicorn
import argparse
import os
from sample_rest_api.app.main import app
from sample_rest_api.app.logger import logger


def run(port, use_memory_db):
    logger.info(f"Starting API server on port {port}")
    uvicorn.run("sample_rest_api.app.main:app", host="0.0.0.0", port=port, reload=True)

def run_cli():
    """Entry point for the swagger-mcp-sample command"""
    parser = argparse.ArgumentParser(description="Run the sample Product-Category API server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=9000, 
        help="Port to run the server on (default: 9000)"
    )
    args = parser.parse_args()
    run(args.port, True)  # Always use memory-db for simplicity


if __name__ == "__main__":
    run_cli()
