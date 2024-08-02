import json
from os import getenv
from typing import Optional, Dict, Any, List

from phi.tools import Toolkit
from phi.utils.log import logger

try:
    import requests
except ImportError:
    raise ImportError("`requests` not installed. Please install using `pip install requests`")


class BraveSearch(Toolkit):
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        country: str = "us",
        search_lang: str = "en",
        ui_lang: str = "en-US",
        safesearch: str = "moderate",
        text_decorations: bool = True,
        spellcheck: bool = True,
        num_results: Optional[int] = None,
        freshness: Optional[str] = None,
        result_filter: Optional[str] = None,
        goggles_id: Optional[str] = None,
        units: Optional[str] = None,
        extra_snippets: Optional[bool] = None,
        summary: bool = True,
        show_results: bool = False,
    ):
        super().__init__(name="brave_search")

        self.api_key = api_key or getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            logger.error("BRAVE_SEARCH_API_KEY not set. Please set the BRAVE_SEARCH_API_KEY environment variable.")

        self.show_results = show_results

        self.country: str = country
        self.search_lang: str = search_lang
        self.ui_lang: str = ui_lang
        self.safesearch: str = safesearch
        self.text_decorations: bool = text_decorations
        self.spellcheck: bool = spellcheck
        self.num_results: Optional[int] = num_results
        self.freshness: Optional[str] = freshness
        self.result_filter: Optional[str] = result_filter
        self.goggles_id: Optional[str] = goggles_id
        self.units: Optional[str] = units
        self.extra_snippets: Optional[bool] = extra_snippets
        self.summary: bool = summary

        self.session = requests.Session()
        self.session.headers.update({"X-Subscription-Token": self.api_key})

        self.register(self.search_brave)

    def search_brave(self, query: str, num_results: int = 10) -> str:
        """Use this function to search Brave Search for a query.

        Args:
            query (str): The query to search for.
            num_results (int): Number of results to return. Defaults to 10.

        Returns:
            str: The search results in JSON format.
        """
        if not self.api_key:
            return "Please set the BRAVE_SEARCH_API_KEY"

        try:
            logger.info(f"Searching Brave for: {query}")
            search_kwargs: Dict[str, Any] = {
                "q": query,
                "country": self.country,
                "search_lang": self.search_lang,
                "ui_lang": self.ui_lang,
                "safesearch": self.safesearch,
                "text_decorations": self.text_decorations,
                "spellcheck": self.spellcheck,
                "count": self.num_results or num_results,
                "freshness": self.freshness,
                "result_filter": self.result_filter,
                "goggles_id": self.goggles_id,
                "units": self.units,
                "extra_snippets": self.extra_snippets,
                "summary": self.summary,
            }
            # Clean up the kwargs
            search_kwargs = {k: v for k, v in search_kwargs.items() if v is not None}
            
            response = self.session.get(self.BASE_URL, params=search_kwargs)
            response.raise_for_status()
            
            brave_results = response.json()
            brave_results_parsed = []
            
            # Parse web results
            for result in brave_results.get("web", {}).get("results", []):
                result_dict = {
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "description": result.get("description"),
                }
                if result.get("extra_snippets"):
                    result_dict["extra_snippets"] = result.get("extra_snippets")
                brave_results_parsed.append(result_dict)
            
            # Parse summarizer results
            summarizer = brave_results.get("summarizer", {})
            if summarizer:
                summary_dict = {
                    "type": summarizer.get("type"),
                    "status": summarizer.get("status"),
                    "title": summarizer.get("title"),
                    "summary": summarizer.get("summary", []),
                    "followups": summarizer.get("followups", []),
                }
                
                # Add enrichments if available
                if "enrichments" in summarizer:
                    summary_dict["enrichments"] = summarizer["enrichments"]
                
                # Add entities_infos if available
                if "entities_infos" in summarizer:
                    summary_dict["entities_infos"] = summarizer["entities_infos"]
                
                brave_results_parsed.append({"summarizer": summary_dict})
            
            parsed_results = json.dumps(brave_results_parsed, indent=4)
            if self.show_results:
                logger.info(parsed_results)
            return parsed_results
        except Exception as e:
            logger.error(f"Failed to search Brave {e}")
            return f"Error: {e}"

    def run(self, query: str, num_results: int = 10) -> str:
        """
        Run a search query and return the results.
        This method is required by the Toolkit class.
        
        :param query: The search query
        :param num_results: Number of results to return
        :return: A string containing the search results in JSON format
        """
        return self.search_brave(query, num_results)


if __name__ == "__main__":
    search = BraveSearch()
    print(search.search_brave("what is the weather in new york city", num_results=5))