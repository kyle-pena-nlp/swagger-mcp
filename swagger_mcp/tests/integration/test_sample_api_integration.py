from unittest.mock import patch
import pytest
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from sample_rest_api.app.main import create_category, read_category, update_category, delete_category, search_products

@pytest.mark.asyncio
async def test_category_crud_operations(mcp_client: OpenAPIMCPServer):
    """Test CRUD operations for categories using the MCP client's call_tool method"""
    handlers = mcp_client._register_handlers()
    call_tool = handlers["call_tool"]
    
    # Mock the category endpoints
    with patch('sample_rest_api.app.main.create_category') as mock_create, \
         patch('sample_rest_api.app.main.read_category') as mock_read, \
         patch('sample_rest_api.app.main.update_category') as mock_update, \
         patch('sample_rest_api.app.main.delete_category') as mock_delete:
        
        # Setup mock return values
        mock_category = {
            "id": "123",
            "name": "Electronics",
            "description": "Electronic products",
            "created_at": "2025-03-26T14:32:18",
            "updated_at": "2025-03-26T14:32:18"
        }
        mock_create.return_value = mock_category
        mock_read.return_value = mock_category
        mock_update.return_value = {**mock_category, "name": "Updated Electronics"}
        mock_delete.return_value = None
        
        # Test create_category
        category = await call_tool("create_category", {
            "name": "Electronics",
            "description": "Electronic products"
        })
        assert category == mock_category
        mock_create.assert_called_once_with(name="Electronics", description="Electronic products")
        
        # Test read_category
        category = await call_tool("read_category", {
            "category_id": "123"
        })
        assert category == mock_category
        mock_read.assert_called_once_with(category_id="123")
        
        # Test update_category
        updated_category = await call_tool("update_category", {
            "category_id": "123",
            "name": "Updated Electronics",
            "description": "Electronic products"
        })
        assert updated_category == {**mock_category, "name": "Updated Electronics"}
        mock_update.assert_called_once_with(category_id="123", name="Updated Electronics", description="Electronic products")
        
        # Test delete_category
        await call_tool("delete_category", {
            "category_id": "123"
        })
        mock_delete.assert_called_once_with(category_id="123")

@pytest.mark.asyncio
async def test_product_search_with_mixed_parameters(mcp_client: OpenAPIMCPServer):
    """Test the product search endpoint with various parameters"""
    handlers = mcp_client._register_handlers()
    call_tool = handlers["call_tool"]
    
    # Mock the search_products endpoint
    with patch('sample_rest_api.app.main.search_products') as mock_search:
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
        mock_search.return_value = mock_products
        
        # Test search with mixed parameters
        products = await call_tool("search_products", {
            "category_id": "123",
            "min_price": 1000,
            "max_price": 2000,
            "sort_by": "price",
            "sort_order": "asc"
        })
        assert products == mock_products
        mock_search.assert_called_once_with(
            category_id="123",
            min_price=1000,
            max_price=2000,
            sort_by="price",
            sort_order="asc"
        )
