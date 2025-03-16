import asyncio
import yfinance as yf
from typing import List, Dict, Any
from app.tool.base import BaseTool


class YahooFinanceApiTool(BaseTool):
    name: str = "yahoo_finance_api_tool"
    description: str = """Interact with Yahoo Finance APIs to fetch stock market data.
Use this tool to retrieve information about stocks, including historical prices, current quotes, and more.
The tool dynamically maps user queries to the appropriate Yahoo Finance API methods."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "(required) The stock ticker symbol (e.g., 'AAPL', 'GOOGL').",
            },
            "data_type": {
                "type": "string",
                "description": "(required) The type of data to fetch (e.g., 'info', 'history', 'actions').",
            },
            "params": {
                "type": "object",
                "description": "(optional) Additional parameters for the API request.",
                "default": {},
            },
        },
        "required": ["ticker", "data_type"],
    }

    async def execute(
        self, ticker: str, data_type: str, params: Dict[str, Any] = {}
    ) -> Any:
        """
        Execute a Yahoo Finance API call and return the response.

        Args:
            ticker (str): The stock ticker symbol (e.g., 'AAPL').
            data_type (str): The type of data to fetch (e.g., 'info', 'history').
            params (dict, optional): Additional parameters for the API request. Default is an empty dictionary.

        Returns:
            Any: The response from the Yahoo Finance API.
        """
        try:
            # Run the API call in a thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._fetch_yahoo_finance_data(ticker, data_type, params),
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def _fetch_yahoo_finance_data(
        self, ticker: str, data_type: str, params: Dict[str, Any]
    ) -> Any:
        """
        Helper function to fetch data from Yahoo Finance API synchronously.

        Args:
            ticker (str): The stock ticker symbol.
            data_type (str): The type of data to fetch.
            params (dict): Additional parameters for the API request.

        Returns:
            Any: The response from the Yahoo Finance API.
        """
        stock = yf.Ticker(ticker)

        if data_type == "info":
            return stock.info
        elif data_type == "history":
            return stock.history(**params)
        elif data_type == "actions":
            return stock.actions
        elif data_type == "dividends":
            return stock.dividends
        elif data_type == "splits":
            return stock.splits
        else:
            return {"error": f"Unsupported data type: {data_type}"}
