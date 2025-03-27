import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestConstValues:
    @pytest.fixture
    def server(self):
        # Define a simple OpenAPI spec with parameters that will be set as const
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test_endpoint",
                        "summary": "Test endpoint",
                        "parameters": [
                            {
                                "name": "required_param",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                },
                                "description": "A required parameter"
                            },
                            {
                                "name": "const_param",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                },
                                "description": "A parameter that will be set as const"
                            },
                            {
                                "name": "other_param",
                                "in": "query",
                                "schema": {
                                    "type": "string"
                                },
                                "description": "Another parameter"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        server = OpenAPIMCPServer(
            'Test Server', 
            openapi_spec,
            const_values={"const_param": "fixed_value"}
        )
        return server

    @pytest.mark.asyncio
    async def test_const_parameter_handling(self, server):
        """Test that const parameters are handled correctly in tool definitions."""
        handlers = server._register_handlers()
        list_tools = handlers["list_tools"]
        tools = await list_tools()
        
        assert len(tools) == 1
        tool = tools[0]
        
        # Verify const parameter is not in tool definition
        tool_params = tool.inputSchema["properties"]
        assert "const_param" not in tool_params
        assert "required_param" in tool_params
        assert "other_param" in tool_params
        
        # Verify required parameters don't include const param
        assert "const_param" not in tool.inputSchema["required"]
        assert "required_param" in tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_const_value_usage(self, server):
        """Test that const values are used when invoking endpoints."""
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]
        
        # Mock the endpoint invocation
        with patch('swagger_mcp.openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            invoker_instance.invoke_with_params.return_value.json.return_value = {"result": "success"}
            invoker_instance.invoke_with_params.return_value.status_code = 200
            
            # Call the tool
            result = await call_tool("test_endpoint", {
                "required_param": "test",
                "other_param": "value"
            })
            
            # Verify the const value was included in the endpoint call
            invoker_instance.invoke_with_params.assert_called_once()
            call_args = invoker_instance.invoke_with_params.call_args[1]
            assert call_args["params"]["const_param"] == "fixed_value"
            assert call_args["params"]["required_param"] == "test"
            assert call_args["params"]["other_param"] == "value"
