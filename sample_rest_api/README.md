# Product-Category REST API

A simple REST API for managing products and categories with OpenAPI specification.

## Features

- CRUD operations for Products and Categories
- Relationship between Products and Categories
- SQLite database for persistence (automatically created on startup)
- Option to use in-memory database (ephemeral, cleared on shutdown)
- Sample data automatically loaded on first run
- OpenAPI documentation (Swagger UI)
- Configurable port (default: 9000)
- JSON response format
- File-based logging with rotation

## Setup

### Quick Setup

Use the provided setup script to automatically install uv, create a virtual environment, and install dependencies:

**On Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows:**
```bash
setup.bat
```

### Manual Setup

1. Clone this repository
2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies using uv:

```bash
# Install uv if you don't have it already
pip install uv

# Use uv to install dependencies
uv pip install -r requirements.txt
```

## Running the API

Start the API server with the default port (9000) and file-based database:

```bash
python run.py
```

Specify a custom port:

```bash
python run.py --port 8080
```

Use an in-memory database (data will be lost when the server stops):

```bash
python run.py --memory-db
```

You can combine options:

```bash
python run.py --port 8080 --memory-db
```

## Database

The API supports two database modes:

1. **File-based SQLite** (default): The database file is stored in the `fast-api-demo` directory as `test.db`. Data persists between server restarts.

2. **In-memory SQLite**: An ephemeral database that exists only while the server is running. All data is lost when the server stops. This is useful for testing or when you want a fresh database on each startup.

On first run, sample data is automatically loaded into the database with categories and products.

## Logging

The API includes a comprehensive logging system with the following features:

- **File-based logs**: All logs are written to the `logs/api.log` file.
- **Log rotation**: When log files reach 5MB, they are rotated (up to 3 backup files are kept).
- **Console output**: Logs are also displayed in the console for easier development and debugging.
- **Detailed endpoint logs**: Each API endpoint logs information about requests, responses, and any errors that occur.
- **Structured logging**: Logs include timestamps, log levels, and contextual information.

### Log Levels

The API uses the following log levels:

- **INFO**: Normal operation logs (startup, shutdown, API calls)
- **WARNING**: Issues that don't prevent the API from functioning but may indicate problems
- **ERROR**: Serious issues that affect operation of the API

You can find the log files in the `logs` directory, which is automatically created when the application starts.

## API Documentation

Once the server is running, you can access the auto-generated Swagger UI documentation at:

```
http://localhost:9000/docs
```

Or the ReDoc documentation at:

```
http://localhost:9000/redoc
```

## API Endpoints

### Categories

- `GET /categories/` - List all categories
- `POST /categories/` - Create a new category
- `GET /categories/{category_id}` - Get a specific category
- `PUT /categories/{category_id}` - Update a category
- `DELETE /categories/{category_id}` - Delete a category

### Products

- `GET /products/` - List all products (with optional filtering)
- `POST /products/` - Create a new product
- `GET /products/{product_id}` - Get a specific product
- `PUT /products/{product_id}` - Update a product
- `DELETE /products/{product_id}` - Delete a product

## Data Models

### Category

```json
{
  "name": "string",
  "description": "string (optional)",
  "id": "string (uuid)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Product

```json
{
  "name": "string",
  "description": "string (optional)",
  "price": "float",
  "category_id": "string (uuid)",
  "in_stock": "boolean (default: true)",
  "id": "string (uuid)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Example Usage

### Create a category

```bash
curl -X 'POST' \
  'http://localhost:9000/categories/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Electronics",
  "description": "Electronic devices and gadgets"
}'
```

### Create a product in that category

```bash
curl -X 'POST' \
  'http://localhost:9000/products/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Smartphone",
  "description": "Latest model smartphone",
  "price": 799.99,
  "category_id": "the-category-id-from-previous-response",
  "in_stock": true
}'
```