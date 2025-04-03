import asyncio
import requests
from typing import Dict, Any
from app.tool.base import BaseTool
import os
from datetime import datetime, timedelta
import webbrowser
from typing import Tuple

from load_dotenv import load_dotenv 
load_dotenv()

class ZohoCRMTool(BaseTool):
    
    name: str = "zoho_crm_tool"
    description: str = """Interact with Zoho CRM APIs to retrieve data using OAuth 2.0 self-client authentication.
    Use this tool to fetch information about modules, records, and other relevant data in your Zoho CRM account."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "(required) The action to perform (e.g., 'get_modules', 'get_records').",
            },
            "module_name": {
                "type": "string",
                "description": "(optional) The name of the module to query (e.g., 'Leads', 'Contacts').",
            },
            "query": {
                "type": "string",
                "description": "(required)A query to filter records using CRM Object Query Language (COQL). or the set of the fields to query for example Account_Name, Email in Deals",
            },
        },
        "required": ["action"],
    }
    

   
        

    async def execute(
        self, action: str, module_name: str = None, query: str = None
    ) -> Dict[str, Any]:
        try:
            (token, token_expiry) = await self._refresh_access_token()
            # just a hack for now to make sure it
            # await self._refresh_access_token()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_zoho_crm_data(token, token_expiry,action, module_name, query),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    # async def _ensure_valid_token(self):
    #     if not self.access_token or (self.token_expiry and datetime.now() >= self.token_expiry):
    #         if not self.refresh_token:
    #             await self._obtain_initial_token()
    #         else:
    #             await self._refresh_access_token()

    # async def _obtain_initial_token(self):
    #     auth_url = f"https://{os.environ.get['ZOHO_AUTH_URL']}/oauth/v2/auth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope=ZohoCRM.modules.ALL"
    #     print("Please visit the following URL to authenticate:")
    #     print(auth_url)
    #     webbrowser.open(auth_url)
        
    #     # Wait for user input with the authorization code
    #     auth_code = input("Enter the authorization code: ")
        
    #     # Exchange the authorization code for tokens
    #     url = "https://accounts.zoho.com/oauth/v2/token"
    #     data = {
    #         "client_id": self.client_id,
    #         "client_secret": self.client_secret,
    #         "redirect_uri": self.redirect_uri,
    #         "grant_type": "authorization_code",
    #         "code": auth_code
    #     }
    #     response = requests.post(url, data=data)
    #     if response.status_code == 200:
    #         token_data = response.json()
    #         self.access_token = token_data["access_token"]
    #         self.refresh_token = token_data["refresh_token"]
    #         self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
    #     else:
    #         raise Exception("Failed to obtain initial token")

    async def _refresh_access_token(self)->Tuple[str, datetime]:
        url = f"https://{os.environ['ZOHO_AUTH_URL']}/oauth/v2/token"
        
        client_id = os.environ.get("ZOHO_CLIENT_ID")
        client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
        # self.redirect_uri = os.environ.get("ZOHO_REDIRECT_URI")
        access_token = os.environ.get("ZOHO_ACCESS_TOKEN")
        refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        token_expiry = None
        
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            (access_token,token_expiry)  = (token_data["access_token"], datetime.now() + timedelta(seconds=token_data["expires_in"]))
            return (access_token,token_expiry)
        else:
            raise Exception("Failed to refresh access token")

    def _fetch_zoho_crm_data(self, token:str, token_expiry: datetime, action: str, module_name: str = None, query: str = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        }

        if action == "get_modules":
            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/settings/modules"
            response = requests.get(url, headers=headers)
            return response.json()

        elif action == "get_records":
            if not module_name:
                return {"error": "Module name is required for retrieving records."}

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/{module_name}"
            print (f"Calling API {url}")
            if query:
                url += f"?fields={query}"

            print (f"Calling API {url}")
            response = requests.get(url, headers=headers)
            return response.json()

        elif action == "query_records":
            if not query:
                return {"error": "COQL query is required for querying records."}

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/coql"
            payload = {"select_query": query}

            response = requests.post(url, headers=headers, json=payload)
            return response.json()

        else:
            return {"error": f"Unsupported action: {action}"}
