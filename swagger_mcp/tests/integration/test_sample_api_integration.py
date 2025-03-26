from unittest.mock import patch
import pytest, json
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from sample_rest_api.app.main import app

@pytest.mark.asyncio
async def test_category_crud_operations(mcp_client: OpenAPIMCPServer):
    """Test CRUD operations for categories using the MCP client's call_tool method"""
    handlers = mcp_client._register_handlers()
    call_tool = handlers["call_tool"]
    list_tools = handlers["list_tools"]
    
    # Setup mock return values
    mock_category = {
        "id": "123",
        "name": "Electronics",
        "description": "Electronic products",
        "created_at": "2025-03-26T14:32:18",
        "updated_at": "2025-03-26T14:32:18"
    }
    mock_updated_category = {**mock_category, "name": "Updated Electronics"}
    
    async def mock_create(*args, **kwargs):
        return mock_category
    
    async def mock_read(*args, **kwargs):
        return mock_category
    
    async def mock_update(*args, **kwargs):
        return mock_updated_category
    
    async def mock_delete(*args, **kwargs):
        return None
    
    # Find the route handlers
    create_handler = next(route for route in app.routes if route.path == "/categories/" and route.methods == {"POST"})
    read_handler = next(route for route in app.routes if route.path == "/categories/{category_id}" and route.methods == {"GET"})
    update_handler = next(route for route in app.routes if route.path == "/categories/{category_id}" and route.methods == {"PUT"})
    delete_handler = next(route for route in app.routes if route.path == "/categories/{category_id}" and route.methods == {"DELETE"})
    
    # Mock the category endpoints
    with patch.object(create_handler, "endpoint", mock_create), \
         patch.object(read_handler, "endpoint", mock_read), \
         patch.object(update_handler, "endpoint", mock_update), \
         patch.object(delete_handler, "endpoint", mock_delete):
        
        # Test create_category
        category = await call_tool("create_category_categories__post", {
            "name": "Electronics",
            "description": "Electronic products"
        })
        
        # Test read_category
        category = await call_tool("read_category_categories__category_id__get", {
            "category_id": "123"
        })
        
        # Test update_category
        updated_category = await call_tool("update_category_categories__category_id__put", {
            "category_id": "123",
            "name": "Updated Electronics",
            "description": "Electronic products"
        })
        
        # Test delete_category
        await call_tool("delete_category_categories__category_id__delete", {
            "category_id": "123"
        })

@pytest.mark.asyncio
async def test_product_search_with_mixed_parameters(mcp_client: OpenAPIMCPServer):
    """Test the product search endpoint with various parameters"""
    handlers = mcp_client._register_handlers()
    call_tool = handlers["call_tool"]
    
    # Setup mock return value
    mock_products = [
        {
            "category_id": "123",
            "id": "456",
            "name": "Gaming Laptop",
            "description": "High-performance gaming laptop",
            "price": 1499.99,
            "created_at": "2025-03-26T14:32:18",
            "updated_at": "2025-03-26T14:32:18"
        }
    ]
    
    async def mock_search(*args, **kwargs):
        return {
            "products": mock_products,
            "total_count": len(mock_products),
            "search_metadata": {
                "page": 1,
                "items_per_page": 10,
                "total_pages": 1,
                "sort_by": "price",
                "sort_order": "asc",
                "filters_applied": {
                    "query": None,
                    "min_price": 1000,
                    "max_price": 2000
                }
            }
        }
    
    # Find the search route handler
    search_handler = next(route for route in app.routes if route.path == "/products/search/{category_id}" and route.methods == {"POST"})
    
    # Mock the search endpoint
    with patch.object(search_handler, "endpoint", mock_search):
        # Test search with mixed parameters
        products = await call_tool("search_products_products_search__category_id__post", {
            "category_id": "123",
            "min_price": 1000,
            "max_price": 2000,
            "sort_by": "price",
            "sort_order": "asc"
        })

@pytest.mark.asyncio
async def test_create_category_categories__post_has_required_fields(mcp_client: OpenAPIMCPServer):
    """Test that the create_category endpoint has required fields"""
    handlers = mcp_client._register_handlers()
    list_tools = handlers["list_tools"]
    
    # Test create_category
    tools = await list_tools()
    create_category_tool = next(tool for tool in tools if tool.name == "create_category_categories__post")
    
    # Check that the category has the required fields
    print(create_category_tool)
    assert create_category_tool.name == "create_category_categories__post"
    assert set(create_category_tool.inputSchema["properties"]) == set(["name", "description"])