import requests
import json
import time
import os
import webbrowser
import logging
from typing import Dict, Any, Optional, List, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenStorage:
    """
    Class for storing and retrieving OAuth tokens.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize the token storage.
        
        Args:
            storage_dir: Directory to store token files in. Defaults to user's home directory.
        """
        if storage_dir is None:
            # Use user's home directory by default
            home_dir = os.path.expanduser("~")
            self.storage_dir = os.path.join(home_dir, ".openapi_mcp_tokens")
        else:
            self.storage_dir = storage_dir
            
        # Create the storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_token_path(self, client_id: str, service_name: Optional[str] = None) -> str:
        """
        Get the path to the token file.
        
        Args:
            client_id: OAuth client ID
            service_name: Optional service name to include in the filename
            
        Returns:
            Path to the token file
        """
        if service_name:
            filename = f"{service_name}_{client_id}_token.json"
        else:
            filename = f"{client_id}_token.json"
        return os.path.join(self.storage_dir, filename)
    
    def save_token(self, client_id: str, token_data: Dict[str, Any], service_name: Optional[str] = None) -> None:
        """
        Save an OAuth token to disk.
        
        Args:
            client_id: OAuth client ID
            token_data: Token data to save
            service_name: Optional service name to include in the filename
        """
        token_path = self._get_token_path(client_id, service_name)
        
        # Add expiry timestamp if not present but we have expires_in
        if 'expires_at' not in token_data and 'expires_in' in token_data:
            token_data['expires_at'] = int(time.time()) + token_data['expires_in']
        
        with open(token_path, 'w') as f:
            json.dump(token_data, f)
    
    def load_token(self, client_id: str, service_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load an OAuth token from disk.
        
        Args:
            client_id: OAuth client ID
            service_name: Optional service name to include in the filename
            
        Returns:
            Token data or None if no token is stored
        """
        token_path = self._get_token_path(client_id, service_name)
        
        if not os.path.exists(token_path):
            return None
        
        try:
            with open(token_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.error(f"Failed to load token from {token_path}")
            return None
    
    def delete_token(self, client_id: str, service_name: Optional[str] = None) -> None:
        """
        Delete an OAuth token from disk.
        
        Args:
            client_id: OAuth client ID
            service_name: Optional service name to include in the filename
        """
        token_path = self._get_token_path(client_id, service_name)
        
        if os.path.exists(token_path):
            os.remove(token_path)


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""
    
    # This will be set by the OAuth handler when starting the server
    authorization_code = None
    error = None
    
    def do_GET(self):
        """Handle GET requests to the callback URL."""
        query_components = parse_qs(urlparse(self.path).query)
        
        # Check for error
        if 'error' in query_components:
            CallbackHandler.error = query_components['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body>
            <h1>Authorization Failed</h1>
            <p>Error: {CallbackHandler.error}</p>
            <p>You can close this window now.</p>
            </body>
            </html>
            """.encode())
            return
        
        # Extract authorization code
        if 'code' in query_components:
            CallbackHandler.authorization_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head><title>Authorization Successful</title></head>
            <body>
            <h1>Authorization Successful</h1>
            <p>You have successfully authorized the application. You can close this window now.</p>
            </body>
            </html>
            """.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head><title>Authorization Failed</title></head>
            <body>
            <h1>Authorization Failed</h1>
            <p>No authorization code was received.</p>
            <p>You can close this window now.</p>
            </body>
            </html>
            """.encode())
    
    # Silence the server logs
    def log_message(self, format, *args):
        pass


class OAuthHandler:
    """
    Handler for OAuth 2.0 authorization code flow.
    """
    
    def __init__(self, token_storage: Optional[TokenStorage] = None):
        """
        Initialize the OAuth handler.
        
        Args:
            token_storage: TokenStorage instance for storing and retrieving tokens
        """
        self.token_storage = token_storage or TokenStorage()
        self.callback_server = None
        self.callback_thread = None
    
    def _start_callback_server(self, port: int = 8000) -> None:
        """
        Start an HTTP server to handle the OAuth callback.
        
        Args:
            port: Port to listen on
        """
        # Reset the class variables
        CallbackHandler.authorization_code = None
        CallbackHandler.error = None
        
        # Create and start the server in a separate thread
        self.callback_server = HTTPServer(('localhost', port), CallbackHandler)
        self.callback_thread = threading.Thread(target=self.callback_server.serve_forever)
        self.callback_thread.daemon = True
        self.callback_thread.start()
        
        logger.info(f"Started callback server on http://localhost:{port}")
    
    def _stop_callback_server(self) -> None:
        """Stop the callback HTTP server."""
        if self.callback_server:
            self.callback_server.shutdown()
            self.callback_server.server_close()
            logger.info("Stopped callback server")
    
    def perform_auth_code_flow(self, 
                              client_id: str, 
                              client_secret: str,
                              auth_url: str,
                              token_url: str,
                              redirect_uri: str = "http://localhost:8000/callback",
                              scope: Optional[str] = None,
                              service_name: Optional[str] = None,
                              port: int = 8000) -> Dict[str, Any]:
        """
        Perform the OAuth 2.0 authorization code flow.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            auth_url: Authorization endpoint URL
            token_url: Token endpoint URL
            redirect_uri: Redirect URI
            scope: OAuth scope(s)
            service_name: Optional service name for token storage
            port: Port to run the callback server on
            
        Returns:
            Dictionary containing the access token and related data
            
        Raises:
            Exception: If the authorization fails
        """
        # Check for existing valid token
        existing_token = self.token_storage.load_token(client_id, service_name)
        if existing_token and 'access_token' in existing_token:
            # Check if the token is still valid
            if 'expires_at' in existing_token and time.time() < existing_token['expires_at']:
                logger.info("Using existing valid access token")
                return existing_token
            
            # If the token has a refresh token, try to refresh it
            if 'refresh_token' in existing_token:
                try:
                    refreshed_token = self.refresh_token(
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=existing_token['refresh_token'],
                        token_url=token_url,
                        service_name=service_name
                    )
                    if refreshed_token:
                        return refreshed_token
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    # Continue with the authorization flow if refresh failed
        
        # Start the callback server
        self._start_callback_server(port)
        
        try:
            # Build the authorization URL
            auth_params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
            }
            
            if scope:
                auth_params['scope'] = scope
            
            # Convert params to query string
            auth_query = '&'.join(f"{key}={value}" for key, value in auth_params.items())
            full_auth_url = f"{auth_url}{'?' if '?' not in auth_url else '&'}{auth_query}"
            
            # Open the browser for the user to authorize
            logger.info(f"Opening browser for authorization: {full_auth_url}")
            webbrowser.open(full_auth_url)
            
            # Wait for the callback to receive the authorization code
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            while not CallbackHandler.authorization_code and not CallbackHandler.error:
                if time.time() - start_time > max_wait_time:
                    raise Exception("Timed out waiting for authorization")
                time.sleep(0.1)
            
            # Check for errors
            if CallbackHandler.error:
                raise Exception(f"Authorization failed: {CallbackHandler.error}")
            
            # Exchange the authorization code for an access token
            logger.info("Exchanging authorization code for access token")
            token_params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': CallbackHandler.authorization_code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(token_url, data=token_params)
            response.raise_for_status()
            token_data = response.json()
            
            # Save the token
            self.token_storage.save_token(client_id, token_data, service_name)
            
            return token_data
            
        finally:
            # Always stop the callback server
            self._stop_callback_server()
    
    def refresh_token(self,
                     client_id: str,
                     client_secret: str,
                     refresh_token: str,
                     token_url: str,
                     service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh an OAuth 2.0 access token.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            refresh_token: Refresh token
            token_url: Token endpoint URL
            service_name: Optional service name for token storage
            
        Returns:
            Dictionary containing the new access token and related data
            
        Raises:
            Exception: If the refresh fails
        """
        logger.info("Refreshing access token")
        
        token_params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=token_params)
        response.raise_for_status()
        token_data = response.json()
        
        # If the refresh response doesn't include a refresh token, keep the old one
        if 'refresh_token' not in token_data:
            token_data['refresh_token'] = refresh_token
        
        # Save the new token
        self.token_storage.save_token(client_id, token_data, service_name)
        
        return token_data
    
    def get_access_token(self,
                        client_id: str,
                        client_secret: str,
                        auth_url: str,
                        token_url: str,
                        redirect_uri: str = "http://localhost:8000/callback",
                        scope: Optional[str] = None,
                        service_name: Optional[str] = None,
                        force_refresh: bool = False) -> str:
        """
        Get an OAuth 2.0 access token, refreshing or reauthorizing if necessary.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            auth_url: Authorization endpoint URL
            token_url: Token endpoint URL
            redirect_uri: Redirect URI
            scope: OAuth scope(s)
            service_name: Optional service name for token storage
            force_refresh: Whether to force a token refresh
            
        Returns:
            Access token string
            
        Raises:
            Exception: If the authorization fails
        """
        # Check for existing valid token
        existing_token = None if force_refresh else self.token_storage.load_token(client_id, service_name)
        
        if existing_token and 'access_token' in existing_token:
            # Check if the token is still valid
            if 'expires_at' in existing_token and time.time() < existing_token['expires_at']:
                logger.info("Using existing valid access token")
                return existing_token['access_token']
            
            # If the token has a refresh token, try to refresh it
            if 'refresh_token' in existing_token:
                try:
                    refreshed_token = self.refresh_token(
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=existing_token['refresh_token'],
                        token_url=token_url,
                        service_name=service_name
                    )
                    return refreshed_token['access_token']
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    # Continue with the authorization flow if refresh failed
        
        # Either no token exists, or it's expired and can't be refreshed
        # Perform the full authorization flow
        token_data = self.perform_auth_code_flow(
            client_id=client_id,
            client_secret=client_secret,
            auth_url=auth_url,
            token_url=token_url,
            redirect_uri=redirect_uri,
            scope=scope,
            service_name=service_name
        )
        
        return token_data['access_token']

    def extract_oauth_urls_from_scheme(self, scheme: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Dict[str, str]]:
        """
        Extract authorization URL, token URL, and scopes from an OAuth scheme.
        Handles both OpenAPI 3.0 and 2.0 (Swagger) formats.
        
        Args:
            scheme: OAuth security scheme object
            
        Returns:
            Tuple of (auth_url, token_url, scopes)
        """
        auth_url = None
        token_url = None
        scopes = {}
        
        if 'flows' in scheme:
            # OpenAPI 3.0 style
            flow_type = 'authorizationCode' if 'authorizationCode' in scheme['flows'] else 'accessCode'
            flow = scheme['flows'][flow_type]
            auth_url = flow.get('authorizationUrl')
            token_url = flow.get('tokenUrl')
            scopes = flow.get('scopes', {})
        else:
            # OpenAPI 2.0 (Swagger) style like in Slack's API
            auth_url = scheme.get('authorizationUrl')
            token_url = scheme.get('tokenUrl')
            scopes = scheme.get('scopes', {})
            
        return auth_url, token_url, scopes 