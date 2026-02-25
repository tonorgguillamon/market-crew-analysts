from crewai_tools import SerperDevTool, WebsiteSearchTool, TavilySearchTool, ScrapeWebsiteTool
from crewai.tools import tool
import yfinance as yf

# 1. Search Tool: Restrict to high-signal financial domains
search_tool = SerperDevTool(
    n_results=5
)

# 2. Website Search: Tailor it for specific deep-dives
# This tool allows agents to "crawl" a specific page if they find a good link.
"""
web_tool = WebsiteSearchTool(
    config={
        "options": {
            "wait_until": "networkidle", # Ensure charts/JS data load
            "headers": {
                "User-Agent": "MarketPulse/1.0 (Institutional Research Bot)"
            }
        }
    }
)
"""

webscraper_tool = ScrapeWebsiteTool()

trusted_finance_search = TavilySearchTool(
    include_domains=[
        "bloomberg.com", 
        "reuters.com", 
        "cnbc.com", 
        "wsj.com",
        "finance.yahoo.com",
        "investing.com"
    ],
    search_depth="basic",
    topic="finance"
)

@tool("stock_price_tool")
def stock_price_tool(ticker: str):
    """Fetches real-time price, volume, and 52-week highs/lows for a ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "price": info.get("currentPrice"),
        "volume": info.get("volume"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow")
    }