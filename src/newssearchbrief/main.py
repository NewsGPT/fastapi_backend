from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated
from utils import NewsSearchHelper, GPTBriefStaticHelper

import settings

app = FastAPI()
# initilize the app with environments

# Define allowed origins
origins = [
    '*'
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_app(app: FastAPI) -> None:
    import os
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    # get the environment
    env = os.getenv("ENV", "local")
    env_file = Path(".") / f".env.{env}"
    if env_file.is_file():
        load_dotenv(env_file)

    # get the environment variables
    settings.NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    settings.NEWSAPI_URL = os.getenv("NEWSAPI_URL")
    settings.OPENAI_APIKEY = os.getenv("OPENAI_APIKEY")
    settings.OPENAI_ORG = os.getenv("OPENAI_ORG")

    # check the environment variables
    if not settings.NEWSAPI_KEY:
        print("API_KEY is not set.")
        sys.exit(1)
    if not settings.NEWSAPI_URL:
        print("API_URL is not set.")
        sys.exit(1)
    if not settings.OPENAI_ORG:
        print("OPENAI_ORG is not set.")
        sys.exit(1)
    if not settings.OPENAI_APIKEY:
        print("OPENAI_APIKEY is not set.")
        sys.exit(1)


init_app(app)

newsSearchHelper = NewsSearchHelper(settings.NEWSAPI_URL, settings.NEWSAPI_KEY)

GPTBriefStaticHelper.init_globally(settings.OPENAI_ORG, settings.OPENAI_APIKEY, "prompt_tmpl.txt")





@app.get("/")
async def root():
    return {"message": "Hello World"}

# the endpoint of given a query and return the news search results


@app.get("/search_news/")
async def search(query: Annotated[str, Query(min_length=3, max_length=50)], 
                 count: int | None = 10, 
                 mkt: str | None = "en-us"
            ):
    return newsSearchHelper.search(query, mkt, count)

@app.get("/brief_news/")
async def brief(query: Annotated[str, Query(min_length=3, max_length=50)], 
                count: int | None = 10, 
                mkt: str | None = "en-us"
            ):
    news_items = newsSearchHelper.search(query, mkt, count)
    return GPTBriefStaticHelper.brief_by_news(news_items)
