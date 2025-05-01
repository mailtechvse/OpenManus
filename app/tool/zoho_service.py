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
                "description": "(required) The action to perform ('get_modules','get_metadata'','get_deals', 'get_leads'). If the module name is not in the list that you intend to call you can form a get uri that appends to /crm/v7/ uri and you can pass parameters to it to check the data. This is the flexibility to run. In such a case the module name is the uri that needs to be appended to the uri. For example to to getch the files you can call action as 'get' and 'module_name' as 'files' so the uri would be /crm/v7/files ",
            },
            "module_name": {
                "type": "string",
                "description": "(Optional) The name of the module to query (e.g., 'Leads', 'Deals', 'Contacts').",
            },
            "fields": {
                "type": "string",
                "description": """(Optional) comma separated list of fields to be fetched from the module. This is only used with get_records action. For example 'id, name, email' will fetch the id, name and email fields from the module""",
                
                
            },
            "parameters": {
                "type": "string",
                "description": """(Optional) '&' separated list of parameters to be passed to the module. This is only used with get_records action. For example 'id=value&name=& email' will fetch the id, name and email fields from the module
                Additionally you could use the parameters for querying the pages with the records to get the total set of the pages page=1&per_page=200
                """,
                
                
            },
            "query": {
                "type": "string",
                "description": """(Optional) The query that is required to be passed to query_records action in form of the string. This must be only used with query_records"""
                
            }
        },
        "required": ["action"],
        
    }
    
    # To execute the tool you need to provide the action and the module name and the query
    async def execute(
        self, action: str, module_name: str = None, query: str = None, parameters: str = None, fields: str = None
    ) -> Dict[str, Any]:
        try:
            (token, token_expiry) = await self._refresh_access_token()
            # just a hack for now to make sure it
            # await self._refresh_access_token()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_zoho_crm_data(token, token_expiry,action, module_name, query, parameters),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    async def _ensure_valid_token(self,token_expiry):
        if token_expiry is not None and datetime.now() >= self.token_expiry:
            return await self._refresh_access_token()
            # if not self.refresh_token:
            #     await self._obtain_initial_token()
            # else:
            

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
        # access_token = os.environ.get("ZOHO_ACCESS_TOKEN")
        refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        token_expiry = None
        
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        response = requests.post(url, data=data)
        # print (vars(response))
        if response.status_code == 200:
            token_data = response.json()
            (access_token,token_expiry)  = (token_data["access_token"], datetime.now() + timedelta(seconds=token_data["expires_in"]))
            # here we are going to update the file to add the data to the file
            
            return (access_token,token_expiry)
        else:
            
            raise Exception(f"Failed to refresh access token, Error, will try in next iteration, {response.status_code} {response.text}")

    def _fetch_zoho_crm_data(self, token:str, token_expiry: datetime, action: str, module_name: str = None, query: str = None, parameters:str = None, fields:str = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        }

        # just changing the None type to String
        
        if parameters is None:
            parameters = ""
        if fields is None:
            fields = ""
        if query is None:
            query = ""

        if action == "get_modules":
            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/settings/modules"
            response = requests.get(url, headers=headers)
            return response.json()

        # elif action == "get_records":
        #     if not module_name:
        #         return {"error": "Module name is required for retrieving records."}

        #     if fields == "":
        #         return {"error": "fields are require, please check API Document for the references. You need to send the data with fields"}

        #     url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/{module_name}"
        #     url = url+"?fields="+fields+"&"+parameters
            
        #     print (f"Calling API {url}")

        #     # if query:
        #     #     url += f"?fields={query}"
 
            
        #     response = requests.get(url, headers=headers)
        #     return response.json()
        
        elif action == "get_leads":
            #overriding the module_name
            module_name = "Leads"
            if not module_name:
                return {"error": "Module name is required for retrieving records."}

            if fields == "":
                # return {"error": "fields are require, please check API Document for the references. You need to send the data with fields"}
                fields="First_Name,Lead_Name,Last_Name,Email"
                
            if parameters == "":
                parameters = "page=1&per_page=200"

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/{module_name}"
            url = url+"?fields="+fields+"&"+parameters
            
            # print (f"Calling API {url}")

            # if query:
            #     url += f"?fields={query}"
 
            
            response = requests.get(url, headers=headers)
            return response.json()
        
        elif action == "get_deals":
            #overriding the module_name
            module_name = "Deals"
            if not module_name:
                return {"error": "Module name is required for retrieving records."}

            if fields == "":
                # return {"error": "fields are require, please check API Document for the references. You need to send the data with fields"}
                fields="Deal_Name,Amount,Currency,Stage,Contact"
                
            if parameters == "":
                parameters = "page=1&per_page=200"

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/{module_name}"
            url = url+"?fields="+fields+"&"+parameters
            
            # print (f"Calling API {url}")
# 
            # if query:
            #     url += f"?fields={query}"
 
            
            response = requests.get(url, headers=headers)
            return response.json()
        
        elif action == "get_metadata":
            if not module_name:
                return {"error": "Module name is required for retrieving records."}

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/settings/modules/{module_name}"

            

            response = requests.get(url+"?fields="+parameters, headers=headers)
            return response.json()

        elif action == "query_records":
            if not query:
                return {"error": "COQL query is required for querying records."}

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/coql"
            payload = query

            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        
    
        else:
            
            # this is the case when the module is not in the list but can directly be called in the GET API
            if not module_name:
                return {"error": "Module name is required for retrieving records."}

            url = f"https://{os.environ.get("ZOHO_API_URL")}/crm/v7/{module_name}"
            # print (f"Calling API {url}")
            # if query:
            #     url += f"?fields={query}"

            # print (f"Calling API {url}")
            response = requests.get(url+"?"+parameters, headers=headers)
            return response.json()
            
            # return {"error": f"Unsupported action: {action}"}
