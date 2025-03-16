import asyncio
import requests
from typing import List, Dict, Any
from app.tool.base import BaseTool


class CryptoApiTool(BaseTool):
    name: str = "crypto_api_tool"
    description: str = """Interact with cryptocurrency APIs to fetch crypto data.
Use this tool to retrieve information about cryptocurrencies, including prices, market caps, and other relevant data.
The tool dynamically maps user queries to the appropriate crypto API endpoints."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "api_name": {
                "type": "string",
                "description": "(required) The name of the crypto API to use (e.g., 'CoinGecko', 'CoinMarketCap').",
            },
            "endpoint": {
                "type": "string",
                "description": "(required) The specific API endpoint to query (e.g., '/coins/markets', '/global').",
            },
            "params": {
                "type": "object",
                "description": "(optional) Query parameters for the API request.",
                "default": {},
            },
        },
        "required": ["api_name", "endpoint"],
    }

    async def execute(
        self, api_name: str, endpoint: str, params: Dict[str, Any] = {}
    ) -> Any:
        """
        Execute a crypto API call and return the response.

        Args:
            api_name (str): The name of the crypto API to use (e.g., 'CoinGecko').
            endpoint (str): The specific API endpoint to query (e.g., '/coins/markets').
            params (dict, optional): Query parameters for the API request. Default is an empty dictionary.

        Returns:
            Any: The response from the crypto API.
        """
        try:
            # Run the API call in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_crypto_data(api_name, endpoint, params),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _fetch_crypto_data(
        self, api_name: str, endpoint: str, params: Dict[str, Any]
    ) -> Any:
        """
        Helper function to fetch data from the crypto API synchronously.

        Args:
            api_name (str): The name of the crypto API to use.
            endpoint (str): The specific API endpoint to query.
            params (dict): Query parameters for the API request.

        Returns:
            Any: The response from the crypto API.
        """
        if api_name == "CoinGecko":
            base_url = "https://api.coingecko.com/api/v2"
        # elif api_name == "CoinMarketCap":
        #     base_url = "https://pro-api.coinmarketcap.com/v1"  # Needs API Key
        else:
            return {"error": f"Unsupported API: {api_name}"}

        url = f"{base_url}{endpoint}"

        headers = {}
        # if api_name == "CoinMarketCap":
        #     headers = {"X-CMC_PRO_API_KEY": "YOUR_API_KEY"}  # Replace with your API key

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
