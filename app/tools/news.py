from typing import Optional, Dict, List
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
import json
import requests


class NewsRetrievalTool(BaseTool):
    """Tool that retrieves the latest news."""

    name: str = "get_news"
    description: str = (
        "This tool is used instead of Bing search tool when News are mentioned. "
        "It is used when phrases like 'What is happening in the world?', 'What is the news?', "
        "'What is the latest news?', 'What is happening in the world today?', 'What is the news today?', "
        "'What is the latest news today?' are used. "
        "Input should be a search query. "
        "Use search query 'trendingtopics' if nothing specific is needed. "
        "Use search query 'category __TOPIC__' if news about general news category is required. "
        "For example 'category sports', 'category business', 'category entertainment'. "
        "Output is a JSON array of the query results."
    )
    results_count: int = 10
    bing_search_url: str
    subscription_key: str

    def _run(
        self,
        search_query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Retrieve the latest news articles based on a search query.

        Args:
            search_query: A string representing the search query.
            run_manager: An optional CallbackManagerForToolRun object.

        Returns:
            A JSON string representing a list of news articles.
        """

        search_parameters: Dict[str, str] = {
            'mkt': 'en-US',
            'cc': 'Germany',
            'safeSearch': 'Off',
            'setLang': 'en-US',
            'sortBy': 'Date',
        }

        if search_query.startswith('category'):
            search_parameters['category'] = search_query.replace('category', '').strip()
            url_suffix: str = ""
        elif search_query == "trendingtopics":
            search_parameters['count'] = str(self.results_count)
            url_suffix: str = "/trendingtopics"
        else:
            search_parameters['count'] = str(self.results_count)
            search_parameters['q'] = search_query
            search_parameters['originalImg'] = 'No'
            search_parameters['freshness'] = 'Week'
            url_suffix: str = "/search"

        url: str = f"{self.bing_search_url}{url_suffix}"

        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        response = requests.get(url, headers=headers, params=search_parameters)
        response.raise_for_status()
        news_articles: dict = json.loads(response.text)

        if len(news_articles) == 0:
            return "Didn't find any news articles"

        formatted_news_articles: List[dict] = []
        for article_number, article in enumerate(news_articles["value"], start=1):
            article_content: dict = {'number': article_number, 'title': article['name']}
            if 'isBreakingNews' in article:
                article_content['isBreakingNews'] = article['isBreakingNews']
            if 'description' in article:
                article_content['description'] = article['description']
            if 'datePublished' in article:
                article_content['published'] = article['datePublished']
            if 'provider' in article and len(article['provider']) > 0:
                article_content['site'] = article['provider'][0]['name']
            formatted_news_articles.append(article_content)

        return json.dumps(formatted_news_articles)
