import pytest
import os
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

@pytest.fixture
def petstore_spec_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'fixtures', 'petstore.json')

@pytest.fixture
def server(petstore_spec_path):
    server = OpenAPIMCPServer('Test Server', petstore_spec_path)
    return server

@pytest.mark.asyncio
async def test_tools_creation(server):
    """Test that tools are created successfully from the OpenAPI spec"""
    handlers = server._register_handlers()
    list_tools = handlers["list_tools"]
    tools = await list_tools()
    
    assert len(tools) > 0, "Should create at least one tool"
    
    # Verify specific tools we expect from petstore.json
    tool_names = {tool.name for tool in tools}
    expected_tools = {"addPet", "updatePet", "getPetById", "uploadFile"}
    assert expected_tools.issubset(tool_names), f"Missing expected tools. Found: {tool_names}"

@pytest.mark.asyncio
async def test_tool_structure(server):
    """Test that each tool has the required attributes"""
    handlers = server._register_handlers()
    list_tools = handlers["list_tools"]
    tools = await list_tools()
    
    for tool in tools:
        assert tool.name, "Tool should have a name"
        assert tool.description, "Tool should have a description"
        assert isinstance(tool.inputSchema, dict), "Tool should have an input schema"
        assert "properties" in tool.inputSchema, "Input schema should have properties"
        
        # Verify tool description format for specific endpoints
        if tool.name == "addPet":
            assert "Add a new pet to the store" in tool.description, "addPet should have correct description"
        elif tool.name == "updatePet":
            assert "Update an existing pet" in tool.description, "updatePet should have correct description"
        elif tool.name == "getPetById":
            assert "Find pet by ID" in tool.description, "getPetById should have correct description"

@pytest.mark.asyncio
async def test_tool_schema_properties(server):
    """Test that tool schemas have proper property structures"""
    handlers = server._register_handlers()
    list_tools = handlers["list_tools"]
    tools = await list_tools()
    
    for tool in tools:
        properties = tool.inputSchema.get('properties', {})
        
        # Verify specific parameter schemas
        if tool.name == "getPetById":
            assert "petId" in properties, "getPetById should have 'petId' parameter"
            pet_id_schema = properties["petId"]
            assert pet_id_schema.get("type") == "integer", "petId should be integer type"
            assert "description" in pet_id_schema, "petId should have description"
            assert pet_id_schema.get("format") == "int64", "petId should have int64 format"
            
        elif tool.name == "uploadFile":
            assert "petId" in properties, "uploadFile should have 'petId' parameter"
            assert "additionalMetadata" in properties, "uploadFile should have 'additionalMetadata' parameter"
            assert "file" in properties, "uploadFile should have 'file' parameter"
            
        # General schema validation
        for param_name, param_schema in properties.items():
            assert isinstance(param_name, str), "Parameter name should be a string"
            assert isinstance(param_schema, dict), "Parameter schema should be a dictionary"
            if 'description' in param_schema:
                assert isinstance(param_schema['description'], str), "Description should be a string"