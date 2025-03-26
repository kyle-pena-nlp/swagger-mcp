import uvicorn
import argparse
import os

def run(port, use_memory_db):
    if not use_memory_db:
        raise Exception("Memory database must be enabled")

    # Set environment variable for in-memory database if requested
    if use_memory_db:
        print("Using in-memory database (data will be lost when server stops)")
        os.environ["MEMORY_DB"] = "true"
    
    print(f"Starting API server on port {port}")
    uvicorn.run("sample_rest_api.app.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Product-Category API server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=9000, 
        help="Port to run the server on (default: 9000)"
    )
    args = parser.parse_args()
    run(args.port, True)  # Force memory-db to True since it's required
