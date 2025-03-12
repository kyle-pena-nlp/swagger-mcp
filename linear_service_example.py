import asyncio
import logging
from linear_service import linear_service, LinearClient, LinearService, configure_logging

async def main():
    # Example 0: Configure logging
    print("Configuring logging...")
    
    # Set to DEBUG level to see more detailed logs
    configure_logging(level=logging.DEBUG, log_file="linear_api.log")
    
    # Example 1: Using the singleton instance
    print("\nExample 1: Using the singleton instance")
    
    # Get all teams
    teams = await linear_service.get_teams()
    print(f"Found {len(teams)} teams:")
    for team in teams:
        print(f"- {team['name']} (ID: {team['id']})")
    
    # Search for issues
    search_query = "in:backlog"
    issues = await linear_service.search_issues(search_query)
    print(f"\nFound {len(issues)} issues matching '{search_query}':")
    for issue in issues[:5]:  # Show only first 5 for brevity
        print(f"- {issue.title} (ID: {issue.id})")
    
    # Example 2: Creating your own service instance
    print("\nExample 2: Creating your own service instance")
    
    # Create a custom client with your API key
    # Note: This is just for demonstration, it will use the same API key
    custom_client = LinearClient()
    
    # Create a custom service with the client
    custom_service = LinearService(client=custom_client)
    
    # Use the custom service
    teams = await custom_service.get_teams()
    print(f"Found {len(teams)} teams using custom service")
    
    # Example 3: Handling errors with logging
    print("\nExample 3: Handling errors with logging")
    
    try:
        # Try to get a non-existent issue
        await linear_service.get_issue("non-existent-id")
    except Exception as e:
        print(f"Caught error: {str(e)}")
        print("The error details have been logged to the log file and console")
    
    # Example 4: Creating an issue
    # Uncomment the following code to create an actual issue
    """
    if teams:
        team_id = teams[0]['id']
        new_issue = await linear_service.create_issue(
            title="Test issue from API",
            description="This is a test issue created using the Linear service layer",
            team_id=team_id
        )
        print(f"\nCreated new issue: {new_issue.title} (ID: {new_issue.id})")
    """

if __name__ == "__main__":
    asyncio.run(main()) 