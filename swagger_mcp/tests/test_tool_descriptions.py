import pytest
import os
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from mcp.types import Tool

@pytest.fixture
def petstore_spec_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'fixtures', 'petstore.json')

@pytest.fixture
def server(petstore_spec_path):
    server = OpenAPIMCPServer('Test Server', petstore_spec_path)
    return server

@pytest.fixture
def tools(server):
    tools = []
    for operation_id, endpoint in server.simple_endpoints.items():
        if endpoint.deprecated:
            continue
            
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if endpoint.combined_parameter_schema and 'properties' in endpoint.combined_parameter_schema:
            input_schema["properties"] = endpoint.combined_parameter_schema['properties']
            if 'required' in endpoint.combined_parameter_schema:
                input_schema["required"] = endpoint.combined_parameter_schema['required']
        
        description = ""
        if endpoint.summary:
            description = endpoint.summary
        else:
            description = f"{endpoint.method.upper()} {endpoint.path}"
        
        if endpoint.description and endpoint.description.strip():
            if description:
                description += "\n\n"
            description += endpoint.description.strip()
        
        tool = Tool(
            name=operation_id,
            description=description,
            inputSchema=input_schema
        )
        tools.append(tool)
    return tools

@pytest.mark.asyncio
async def test_tools_creation(tools):
    """Test that tools are created successfully from the OpenAPI spec"""
    assert len(tools) > 0, "Should create at least one tool"
    
@pytest.mark.asyncio
async def test_tool_structure(tools):
    """Test that each tool has the required attributes"""
    for tool in tools:
        assert isinstance(tool, Tool)
        assert tool.name, "Tool should have a name"
        assert tool.description, "Tool should have a description"
        assert isinstance(tool.inputSchema, dict), "Tool should have an input schema"
        assert "properties" in tool.inputSchema, "Input schema should have properties"

@pytest.mark.asyncio
async def test_tool_schema_properties(tools):
    """Test that tool schemas have proper property structures"""
    for tool in tools:
        properties = tool.inputSchema.get('properties', {})
        for param_name, param_schema in properties.items():
            assert isinstance(param_name, str), "Parameter name should be a string"
            assert isinstance(param_schema, dict), "Parameter schema should be a dictionary"
            # Optional but common fields
            if 'description' in param_schema:
                assert isinstance(param_schema['description'], str)