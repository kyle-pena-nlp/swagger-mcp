import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("linear_service")

# Default log file path - can be overridden by environment variable
DEFAULT_LOG_FILE = os.getenv("LINEAR_LOG_FILE", "linear_api.log")

def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Configure the logging level and optionally add a file handler.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If provided, logs will be written to this file.
                 If None, will use the DEFAULT_LOG_FILE value.
    """
    # Set the level for the linear_service logger and its children
    logger.setLevel(level)
    
    # If a log file is provided or DEFAULT_LOG_FILE is set, add a file handler
    log_file_path = log_file or DEFAULT_LOG_FILE
    if log_file_path:
        # Check if we already have a file handler to avoid duplicates
        has_file_handler = any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
        
        if not has_file_handler:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file_path}")
    
    logger.info(f"Logging level set to: {logging.getLevelName(level)}")

# Load environment variables
load_dotenv()

# Get Linear API key from environment variables
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
if not LINEAR_API_KEY:
    logger.error("LINEAR_API_KEY environment variable is not set")
    raise ValueError("LINEAR_API_KEY environment variable is not set")

# Linear API base URL
LINEAR_API_URL = "https://api.linear.app/graphql"

# Models for Linear API
class LinearIssue(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    
class LinearComment(BaseModel):
    id: str
    body: str
    user: Optional[Dict[str, Any]] = None
    createdAt: str

class LinearClient:
    def __init__(self, api_key: str = LINEAR_API_KEY):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"{api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger("linear_service.client")
    
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against the Linear API"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        # Log the request (without the full query for brevity)
        self.logger.info(f"Executing GraphQL query with variables: {json.dumps(variables or {})}")
        self.logger.debug(f"Full query: {query}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    LINEAR_API_URL,
                    headers=self.headers,
                    json=payload
                )
                
                # Log response status
                self.logger.info(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_message = f"Linear API error: {response.text}"
                    self.logger.error(error_message)
                    raise Exception(error_message)
                
                response_data = response.json()
                
                # Check for GraphQL errors
                if "errors" in response_data:
                    error_message = f"GraphQL errors: {json.dumps(response_data['errors'])}"
                    self.logger.error(error_message)
                    # Still return the response as it might contain partial data
                    self.logger.debug(f"Response data: {json.dumps(response_data)}")
                    return response_data
                
                # Log success (with limited data for brevity)
                if "data" in response_data:
                    data_keys = list(response_data["data"].keys())
                    self.logger.info(f"Successful response with data keys: {data_keys}")
                    self.logger.debug(f"Full response data: {json.dumps(response_data)}")
                
                return response_data
        except Exception as e:
            error_message = f"Error executing GraphQL query: {str(e)}"
            self.logger.exception(error_message)
            raise

class LinearService:
    def __init__(self, client: LinearClient = None):
        self.client = client or LinearClient()
        self.logger = logging.getLogger("linear_service.service")
    
    async def get_issues(self) -> List[LinearIssue]:
        """Get all Linear issues"""
        self.logger.info("Getting all issues")
        query = """
        query {
            issues {
                nodes {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        try:
            result = await self.client.execute_query(query)
            issues = result.get("data", {}).get("issues", {}).get("nodes", [])
            self.logger.info(f"Retrieved {len(issues)} issues")
            return [LinearIssue(**issue) for issue in issues]
        except Exception as e:
            self.logger.exception("Error getting issues")
            raise

    async def get_issue(self, issue_id: str) -> LinearIssue:
        """Get a specific Linear issue by ID"""
        self.logger.info(f"Getting issue with ID: {issue_id}")
        query = """
        query($id: String!) {
            issue(id: $id) {
                id
                title
                description
                state {
                    id
                    name
                }
                assignee {
                    id
                    name
                }
                team {
                    id
                    name
                }
                priority
            }
        }
        """
        
        variables = {"id": issue_id}
        try:
            result = await self.client.execute_query(query, variables)
            issue_data = result.get("data", {}).get("issue", {})
            
            if not issue_data:
                error_message = f"Issue with ID {issue_id} not found"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            self.logger.info(f"Retrieved issue: {issue_data.get('title', 'Unknown title')}")
            return LinearIssue(**issue_data)
        except Exception as e:
            self.logger.exception(f"Error getting issue with ID {issue_id}")
            raise

    async def get_issue_comments(self, issue_id: str) -> List[LinearComment]:
        """Get comments for a specific Linear issue"""
        self.logger.info(f"Getting comments for issue with ID: {issue_id}")
        query = """
        query($id: String!) {
            issue(id: $id) {
                comments {
                    nodes {
                        id
                        body
                        user {
                            id
                            name
                        }
                        createdAt
                    }
                }
            }
        }
        """
        
        variables = {"id": issue_id}
        try:
            result = await self.client.execute_query(query, variables)
            comments = result.get("data", {}).get("issue", {}).get("comments", {}).get("nodes", [])
            
            self.logger.info(f"Retrieved {len(comments)} comments for issue {issue_id}")
            return [LinearComment(**comment) for comment in comments]
        except Exception as e:
            self.logger.exception(f"Error getting comments for issue with ID {issue_id}")
            raise

    async def search_issues(self, query_string: str) -> List[LinearIssue]:
        """Search for Linear issues based on a query string"""
        self.logger.info(f"Searching issues with query: {query_string}")
        query = """
        query($filter: String!) {
            issueSearch(filter: $filter) {
                nodes {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        variables = {"filter": query_string}
        try:
            result = await self.client.execute_query(query, variables)
            issues = result.get("data", {}).get("issueSearch", {}).get("nodes", [])
            
            self.logger.info(f"Found {len(issues)} issues matching query: {query_string}")
            return [LinearIssue(**issue) for issue in issues]
        except Exception as e:
            self.logger.exception(f"Error searching issues with query: {query_string}")
            raise

    async def create_issue(self, title: str, description: str, team_id: str) -> LinearIssue:
        """Create a new Linear issue"""
        self.logger.info(f"Creating new issue: {title} for team: {team_id}")
        query = """
        mutation($title: String!, $description: String, $teamId: String!) {
            issueCreate(input: {
                title: $title,
                description: $description,
                teamId: $teamId
            }) {
                issue {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        variables = {
            "title": title,
            "description": description,
            "teamId": team_id
        }
        
        try:
            result = await self.client.execute_query(query, variables)
            issue_data = result.get("data", {}).get("issueCreate", {}).get("issue", {})
            
            if not issue_data:
                error_message = "Failed to create issue"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            self.logger.info(f"Created issue with ID: {issue_data.get('id')}")
            return LinearIssue(**issue_data)
        except Exception as e:
            self.logger.exception(f"Error creating issue: {title}")
            raise

    async def update_issue_description(self, issue_id: str, description: str) -> LinearIssue:
        """Update the description of a Linear issue"""
        self.logger.info(f"Updating description for issue with ID: {issue_id}")
        query = """
        mutation($id: String!, $description: String!) {
            issueUpdate(id: $id, input: {
                description: $description
            }) {
                issue {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "description": description
        }
        
        try:
            result = await self.client.execute_query(query, variables)
            issue_data = result.get("data", {}).get("issueUpdate", {}).get("issue", {})
            
            if not issue_data:
                error_message = f"Failed to update issue with ID {issue_id}"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            self.logger.info(f"Updated description for issue: {issue_data.get('title')}")
            return LinearIssue(**issue_data)
        except Exception as e:
            self.logger.exception(f"Error updating description for issue with ID {issue_id}")
            raise

    async def add_comment(self, issue_id: str, body: str) -> LinearComment:
        """Add a comment to a Linear issue"""
        self.logger.info(f"Adding comment to issue with ID: {issue_id}")
        query = """
        mutation($issueId: String!, $body: String!) {
            commentCreate(input: {
                issueId: $issueId,
                body: $body
            }) {
                comment {
                    id
                    body
                    user {
                        id
                        name
                    }
                    createdAt
                }
            }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "body": body
        }
        
        try:
            result = await self.client.execute_query(query, variables)
            comment_data = result.get("data", {}).get("commentCreate", {}).get("comment", {})
            
            if not comment_data:
                error_message = f"Failed to add comment to issue with ID {issue_id}"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            self.logger.info(f"Added comment with ID: {comment_data.get('id')} to issue: {issue_id}")
            return LinearComment(**comment_data)
        except Exception as e:
            self.logger.exception(f"Error adding comment to issue with ID {issue_id}")
            raise

    async def assign_issue(self, issue_id: str, assignee_id: str) -> LinearIssue:
        """Assign a Linear issue to a user"""
        self.logger.info(f"Assigning issue {issue_id} to user {assignee_id}")
        query = """
        mutation($id: String!, $assigneeId: String!) {
            issueUpdate(id: $id, input: {
                assigneeId: $assigneeId
            }) {
                issue {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "assigneeId": assignee_id
        }
        
        try:
            result = await self.client.execute_query(query, variables)
            issue_data = result.get("data", {}).get("issueUpdate", {}).get("issue", {})
            
            if not issue_data:
                error_message = f"Failed to assign issue with ID {issue_id}"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            assignee_name = issue_data.get("assignee", {}).get("name", "Unknown")
            self.logger.info(f"Assigned issue {issue_id} to {assignee_name}")
            return LinearIssue(**issue_data)
        except Exception as e:
            self.logger.exception(f"Error assigning issue {issue_id} to user {assignee_id}")
            raise

    async def change_issue_state(self, issue_id: str, state_id: str) -> LinearIssue:
        """Change the state of a Linear issue"""
        self.logger.info(f"Changing state of issue {issue_id} to state {state_id}")
        query = """
        mutation($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: {
                stateId: $stateId
            }) {
                issue {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                    priority
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "stateId": state_id
        }
        
        try:
            result = await self.client.execute_query(query, variables)
            issue_data = result.get("data", {}).get("issueUpdate", {}).get("issue", {})
            
            if not issue_data:
                error_message = f"Failed to change state of issue with ID {issue_id}"
                self.logger.error(error_message)
                raise ValueError(error_message)
            
            state_name = issue_data.get("state", {}).get("name", "Unknown")
            self.logger.info(f"Changed state of issue {issue_id} to {state_name}")
            return LinearIssue(**issue_data)
        except Exception as e:
            self.logger.exception(f"Error changing state of issue {issue_id} to state {state_id}")
            raise

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams in Linear"""
        self.logger.info("Getting all teams")
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        try:
            result = await self.client.execute_query(query)
            teams = result.get("data", {}).get("teams", {}).get("nodes", [])
            
            self.logger.info(f"Retrieved {len(teams)} teams")
            return teams
        except Exception as e:
            self.logger.exception("Error getting teams")
            raise

    async def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all members of a specific team"""
        self.logger.info(f"Getting members for team with ID: {team_id}")
        query = """
        query($id: String!) {
            team(id: $id) {
                members {
                    nodes {
                        id
                        name
                        email
                    }
                }
            }
        }
        """
        
        variables = {"id": team_id}
        try:
            result = await self.client.execute_query(query, variables)
            members = result.get("data", {}).get("team", {}).get("members", {}).get("nodes", [])
            
            self.logger.info(f"Retrieved {len(members)} members for team {team_id}")
            return members
        except Exception as e:
            self.logger.exception(f"Error getting members for team with ID {team_id}")
            raise

# Create a singleton instance for easy import
linear_service = LinearService()

# Auto-configure logging with default settings if LINEAR_AUTO_LOG environment variable is set
if os.getenv("LINEAR_AUTO_LOG", "true").lower() in ("true", "1", "yes"):
    auto_log_level = getattr(logging, os.getenv("LINEAR_LOG_LEVEL", "INFO"))
    configure_logging(level=auto_log_level, log_file=DEFAULT_LOG_FILE) 