from app.tool.base import BaseTool
import requests
import asyncio

from typing import Dict, List, Tuple, Any
import os

from load_dotenv import load_dotenv

load_dotenv()


# Tool for Notion
class NotionTool(BaseTool):
    name: str = "notion_tool"
    description: str = """Interact with Notion API to manage pages and databases.
    Use this tool to create, retrieve, update, and search pages in Notion.
    Requires API key and database ID."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "(required) The action to perform (e.g., 'query_database', 'create_page').",
            },
            "database_id": {
                "type": "string",
                "description": "(required for 'query_database' and 'create_page') The ID of the Notion database.",
            },
            "page_id": {
                "type": "string",
                "description": "(optional) The ID of the Notion page to retrieve or update.",
            },
            "query": {
                "type": "string",
                "description": "(optional) The query to filter database results.",
            },
            "properties": {
                "type": "object",
                "description": "(optional) Properties for creating or updating a page (e.g., {'Name': {'title': [{'text': {'content': 'My Page'}}]}}).",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, database_id: str = None, page_id: str = None, query: str = None, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a Notion API call and return the response.
        """
        try:
            # Run the API call in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_notion_data(action, database_id, page_id, query, properties),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _fetch_notion_data(self, action: str, database_id: str = None, page_id: str = None, query: str = None, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Helper function to fetch data from the Notion API synchronously.
        """
        NOTION_API_KEY = os.environ.get("NOTION_API_KEY")  # Retrieve Notion API key from environment variables
        NOTION_VERSION = "2022-06-28"  # Or the latest version

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

        if action == "query_database":
            if not database_id:
                return {"error": "Database ID is required for querying."}

            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            payload = {}
            if query:
                payload = {"filter": {"property": "Name", "title": {"contains": query}}}  # Example filter

            response = requests.post(url, headers=headers, json=payload)
            return response.json()

        elif action == "create_page":
            if not database_id or not properties:
                return {"error": "Database ID and properties are required for creating a page."}

            url = "https://api.notion.com/v1/pages"
            payload = {"parent": {"database_id": database_id}, "properties": properties}

            response = requests.post(url, headers=headers, json=payload)
            return response.json()

        elif action == "retrieve_page":
            if not page_id:
                return {"error": "Page ID is required for retrieving a page."}

            url = f"https://api.notion.com/v1/pages/{page_id}"
            response = requests.get(url, headers=headers)
            return response.json()

        else:
            return {"error": f"Unsupported action: {action}"}
        



class NotionDiscoveryTool(BaseTool):
    name: str = "notion_discovery_tool"
    description: str = """Interact with the Notion API to discover database and page IDs.
    Use this tool to automatically retrieve all accessible databases and pages for your integration."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "(optional) A search query to filter results by title or content.",
            },
        },
        "required": [],
    }

    async def execute(self, query: str = None) -> Dict[str, Any]:
        """
        Execute a Notion API call to discover database and page IDs.

        Args:
            query (str, optional): A search query to filter results by title or content.

        Returns:
            Dict[str, Any]: A list of discovered databases and pages with their IDs.
        """
        try:
            # Run the discovery process in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._discover_notion_resources(query),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _discover_notion_resources(self, query: str = None) -> Dict[str, Any]:
        """
        Helper function to fetch data from the Notion API synchronously.

        Args:
            query (str): A search query to filter results.

        Returns:
            Dict[str, Any]: A list of discovered databases and pages with their IDs.
        """
        NOTION_API_KEY = os.environ.get("NOTION_API_KEY")  # Retrieve Notion API key from environment variables
        NOTION_VERSION = "2022-06-28"  # Or the latest version

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

        url = "https://api.notion.com/v1/search"
        
        payload = {
            "filter": {
                "value": "database",  # Search for databases
                "property": "object"
            }
        }

        if query:
            payload["query"] = query

        # Search for databases
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch resources: {response.text}"}

        data = response.json()
        
        # Extract database details
        databases = [
            {"id": result["id"], "title": result["title"][0]["text"]["content"]}
            for result in data["results"]
            if result["object"] == "database"
        ]

        # Search for pages as well (optional)
        payload["filter"]["value"] = "page"  # Update filter for pages
        response_pages = requests.post(url, headers=headers, json=payload)
        
        if response_pages.status_code != 200:
            return {"error": f"Failed to fetch pages: {response_pages.text}"}

        data_pages = response_pages.json()
        
        pages = [
            {"id": result["id"], "title": result["properties"]["title"]["title"][0]["text"]["content"]}
            for result in data_pages["results"]
            if result["object"] == "page"
        ]

        return {
            "databases": databases,
            "pages": pages,
        }



if __name__ == "__main__":
    
    discovery_tool = NotionDiscoveryTool()
    discovery_tool.execute(query="Test Project")