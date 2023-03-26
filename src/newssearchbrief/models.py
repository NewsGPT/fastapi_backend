from pydantic import BaseModel
from typing import List

# define a class to represent the news search results

class NewsSearchResult(BaseModel):
    # contains url, title, description date and thubnail
    url: str 
    title: str 
    description: str | None
    datePublished: str | None
    thumbnail: str | None
    
    
class NewsBriefCluster(BaseModel):
    title: str
    bullets: List[str]
    referedUrls: List[str]
    referredImages: List[str]