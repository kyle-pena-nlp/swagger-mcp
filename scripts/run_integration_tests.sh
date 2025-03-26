#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SAMPLE_API_DIR="$PROJECT_ROOT/sample-rest-api"
API_PID=""

# Function to create and activate a virtual environment
setup_venv() {
    local venv_dir="$1"
    local requirements_file="$2"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$venv_dir" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$venv_dir"
    fi
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    
    # Install requirements if they exist
    if [ -f "$requirements_file" ]; then
        echo "Installing requirements..."
        pip install -r "$requirements_file"
    fi
}

# Function to start the sample REST API
start_sample_api() {
    echo "Starting sample REST API..."
    
    # Set up and activate the API's virtual environment
    setup_venv "$SAMPLE_API_DIR/.venv" "$SAMPLE_API_DIR/requirements.txt"
    
    # Start the API server
    cd "$SAMPLE_API_DIR"
    python app.py > /tmp/sample_api.log 2>&1 &
    API_PID=$!
    cd - > /dev/null
    
    # Wait for the server to start (2 seconds)
    sleep 2
    
    # Check if the process is still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "Failed to start sample REST API. Log output:"
        cat /tmp/sample_api.log
        exit 1
    fi
}

# Function to stop the sample REST API
stop_sample_api() {
    if [ -n "$API_PID" ]; then
        echo "Shutting down sample REST API..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
    fi
}

# Function to run integration tests
run_tests() {
    echo "Running integration tests..."
    pytest swagger_mcp/tests/test_openapi_mcp_integration.py -v
}

# Function to run example scripts
run_examples() {
    echo "Running example scripts..."
    local failed=0
    
    # Run each example script
    for example in "$PROJECT_ROOT"/examples/*.py; do
        # Skip test files
        if [[ $(basename "$example") == test_* ]]; then
            continue
        fi
        
        echo -e "\nRunning example: $(basename "$example")"
        if ! python "$example"; then
            echo "Example $(basename "$example") failed!"
            failed=1
        fi
    done
    
    return $failed
}

# Cleanup function to ensure API is stopped
cleanup() {
    stop_sample_api
}

# Set up cleanup on script exit
trap cleanup EXIT

# Parse command line arguments
RUN_EXAMPLES=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --examples)
            RUN_EXAMPLES=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set up the main project's virtual environment
setup_venv "$PROJECT_ROOT/.venv" "$PROJECT_ROOT/requirements.txt"

# Start the sample REST API
start_sample_api

# Run either tests or examples
if [ $RUN_EXAMPLES -eq 1 ]; then
    run_examples
    exit_code=$?
else
    run_tests
    exit_code=$?
fi

# Exit with the appropriate code
if [ $exit_code -eq 0 ]; then
    echo -e "\nAll tests passed successfully!"
else
    echo -e "\nSome tests failed!"
fi

exit $exit_code
