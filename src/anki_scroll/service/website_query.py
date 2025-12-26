from abc import ABC, abstractmethod
from pydantic import BaseModel
import dspy
import requests
from bs4 import BeautifulSoup
from dspy import Module, Signature
from pathlib import Path

################################ service definition

class WebsiteResult(BaseModel):
    excerpt: str
    title: str
    url: str

class SearchWikipediaService(Module):
    """
    provide a service to search wkipedia pages matching a specific query
    """
    
    @abstractmethod
    def query(self, query: str, articles:int = 3) -> list[WebsiteResult]:
        """
        given a query return a maximum of limit result matching the query
        """
        raise NotImplementedError
    
    def forward(self,  **kwargs):
        """should not be used"""
        raise NotImplementedError
    
    
class QueryWikipedia(Module):
    """
    provide a service to look up specific wikipedia articles
    """
    
    @abstractmethod
    def content(self, url: str) -> str:
        """
        Remove non textual elements from the website 
        except for formatting tags and return the content
        """
        raise NotImplementedError
    
    def forward(self,  **kwargs):
        """should not be used"""
        raise NotImplementedError
    
    
################################  wikipedia

class WikiSearchResult(Signature):
    """
    Use the wikipedia index to find relevant english wikipedia articles relative the query.
    Return the n most relevant ones.
    
    example:
    query: chinese history
    
    articles:
    - https://en.wikipedia.org/wiki/History_of_China
    - https://en.wikipedia.org/wiki/Timeline_of_Chinese_history
    - https://en.wikipedia.org/wiki/Dynasties_of_China
    """
    query: str = dspy.InputField(desc="search query")
    n: int = dspy.InputField(desc="the number of articles to return")
    articles: list[str] = dspy.OutputField(desc="url of the n most relevant articles relative to the query.")



class WikipediaIndex(SearchWikipediaService):
    """
    search wikipedia english articles using an llm and the wikipedia index
    """
    
    def __init__(self, callbacks=None):
        super().__init__(callbacks)
        self.search_agent = dspy.ReAct(WikiSearchResult, [dspy.Tool(_query_wikipedia_index)])
        
        
    def query(self, query: str, limit:int = 5) -> list[WebsiteResult]:
        preds = self.search_agent(query=query, n=limit)
        return [WebsiteResult(excerpt="",title="",url=url) for url in preds.articles]
    
    def forward(self, query: str, limit:int = 5) -> dspy.Prediction:
        websites = self.query(query, limit)
        return dspy.Prediction(websites=[website.url for website in websites])

################ query wikipedia api

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
}
session.headers.update(headers)

_WIKIPEDIA_WIKI_BASE = "https://{language}.wikipedia.org/wiki/{article}"
def _wikipedia_article(article: str, language: str = "en") -> str:
    """
    parameters:
    article -- the name of the article to retrieve ex: china
    """
    
    response = session.get(_WIKIPEDIA_WIKI_BASE.format(language=language, article=article))
    if response.ok:
        html = BeautifulSoup(response.text, "html.parser")
        return html.text
    else:
        return f"article not found: {article}"


_WIKIPEDIA_INDEX_BASE = "https://{language}.wikipedia.org/w/index.php"
def _query_wikipedia_index(terms: list[str], language: str = "en") -> list[WebsiteResult]:
    """
    query the wikipedia index return list of results returned by the index.
    Sometimes, the index return only 1 result if the query match exactly to an article.
    
    params:
    terms -- list of the terms of the query. e.g: china history
    """
    query = " ".join(terms)
    response = session.get(
        _WIKIPEDIA_INDEX_BASE.format(language=language), 
        params={"search":query, "title":"Special:Search"})
    
    parts = Path(response.url).parts
    
    # could be a bit dangerous, but risk is low. We should use a way to parse the url
    if "index.php" in response.url:
        return _parse_index_result_page(response) 
    if parts[-2] == "wiki":
        return [_article_summary(response)]
    raise RuntimeError(f"url do not match expected format: {response.url}")

def _parse_index_result_page(response: requests.Response) -> list[WebsiteResult]:
    "we assume that the response respects index results format"
    if not response.ok:
        raise ValueError("response is wrong")
    
    html = BeautifulSoup(response.text,"html.parser")
    
    websites_results = []
    for result in html.find_all("div", class_="searchResultImage-text"):
        try:
            heading = result.find("div", class_="mw-search-result-heading")
            href = heading.find("a").get("href")
            title = heading.text
            excerpt = result.find("div", class_="searchresult").text
        except AttributeError:
            continue

        websites_results.append(WebsiteResult(excerpt=excerpt, title=title, url=f"https://en.wikipedia.org{href}"))
    return websites_results

def _article_summary(response: requests.Response) -> WebsiteResult:
    if not response.ok:
        raise ValueError("response is wrong")
    html = BeautifulSoup(response.text, "html.parser")
    
    first_p = html.find("p")
    while first_p is not None and len(first_p.text)<50:
        first_p = first_p.find_next("p")
    excerpt = "no text found" if first_p is None else first_p.text
    
    h1 = html.find("h1")
    title = "no title found" if h1 is None else h1.text
    
    return WebsiteResult(excerpt=excerpt,url=response.url, title=title)
        
        


