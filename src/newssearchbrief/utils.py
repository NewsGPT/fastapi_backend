import requests
import openai
import re

from models import NewsSearchResult, NewsBriefCluster
from typing import List

# def a class for news search helper:

class NewsSearchHelper:
    def __init__(self, endpoint, api_key) -> None:
        self.endpoint = endpoint
        self.api_key =  api_key
    
    def search(self, query, mkt="en-us", count=10) -> List[NewsSearchResult]:
        params = "count={}&mkt={}&q={}".format(count, mkt, query)
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        resp = requests.get(self.endpoint, params=params, headers=headers)
        if resp.status_code != 200:
            raise Exception("API response: {}".format(resp.status_code))

        d = resp.json()
        res = []
        for _, i in enumerate(d['value']):
            # cast the result to NewsSearchResult, preventing getting null key error
            url = i.get("url", None)
            title = i.get("name", None)
            description = i.get("description", None)
            dataPublished = i.get("datePublished", None)
            thumbnail = None

            if i.get("image", None):
                if i.get("image").get("thumbnail", None):
                    thumbnail = i.get("image").get("thumbnail").get("contentUrl", None)

            if url is None or title is None:
                continue

            r = NewsSearchResult(url = url,
                                 title = title,
                                 description=description,
                                 dataPublished=dataPublished,
                                 thumbnail=thumbnail
            )
            res.append(r)
        return res

class GPTBriefStaticHelper:

    prompt_tmpl: str = ""

    @staticmethod
    def init_globally(orgid, api_key, prompt_tmpl_file) -> None:
        openai.api_key = api_key
        openai.organization =  orgid
        #readling file from prompt_tmpl, load all the lines into text contents
        with open(prompt_tmpl_file, "r") as f:
            GPTBriefStaticHelper.prompt_tmpl = f.read()

    @staticmethod
    def brief_by_news(news_items: List[NewsSearchResult]) -> str:
        lines = []
        for i, item in enumerate(news_items):
            lines.append("News Item {}:".format(i))
            lines.append(item.title)
            # add extra line break
            lines.append(item.description[:300] if item.description else "")
            lines.append('\n')
        
        list_of_news_str = "\n".join(lines)
        prompt = GPTBriefStaticHelper.prompt_tmpl.format(news_count=len(news_items), list_of_news=list_of_news_str)
        print(prompt)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=1200,
            top_p=0.33,
            frequency_penalty=0,
            presence_penalty=0
        )

        # check if response is  valid:
        if response.choices is None or len(response.choices) == 0:
            return None
        
        return GPTBriefStaticHelper.extract_brief("1." + response.choices[0].text, news_items)

    @staticmethod
    def extract_brief(output_text, news_items) -> List[NewsBriefCluster]:
        """_summary_

        Args:
            output_text (_type_): _description_

        Returns:
            List[NewsBriefCluster]: _description_
        """
        """
        Example of output text
        1. China-Honduras Relations: 
        - Honduras establishes ties with China after Taiwan break
        - China opens ties with Honduras, Taiwan decries monetary demands      
        - Honduras forms diplomatic ties with China after Taiwan break
        Reference: 0, 5, 9

        2. China-Canada Relations:
        - New allegations and a resignation strain already fraught China-Canada relations
        Reference: 1

        3. China Marriage Rates:
        - In China, Marriage Rates Are Down and ‘Bride Prices’ Are Up
        Reference: 2

        4. China-Iran-Saudi Deal:
        - In Their Own Words, Yemen War Rivals See Wary Hope in China-Iran-Saudi Deal
        Reference: 3

        5. Russia-China Cooperation:
        - Russia, China are not creating military alliance, Putin says
        Reference: 4

        6. Japan-China Relations:
        - Japanese man detained in China is Astellas Pharma employee - Kyodo   
        Reference: 7
        
        """
        # parse the output text into list of NewsBriefCluster
        clusters = []
        lines = output_text.split("\n")
        #print(lines)
        start_pat = re.compile(r"^[0-9]+\.")
        ref_pat = re.compile(r'reference:', re.IGNORECASE)
        _start = False
        _end = True

        for line in lines:
            # regex detect if the line start with number among 1-6 and followed a dot
            ref_match = ref_pat.search(line)
            start_match = start_pat.search(line)
            if start_match:
                # new cluster
                title = line[start_match.end():].strip(": ")
                bullets = []
                referedUrls = []
                referredImages = []
                #print(title)
                # if last cluster not close:
                _start = True
                if not _end:
                    raise Exception("Last cluster not end. Parsing completion expection.{}".format(output_text))
                _end = False

            
            elif ref_match:
                if not _start:
                    raise Exception("Cluster has no start. Parsing completion expection.{}".format(output_text))
                _start = False
                    
                # add reference
                #print(line)
                refs = re.findall(r'\d+', line[ref_match.end():])
                for ref in refs:
                    news_idx = int(ref)
                    if news_idx < len(news_items):
                        referedUrls.append(news_items[news_idx].url)
                        referredImages.append(news_items[news_idx].thumbnail)

                clusters.append(NewsBriefCluster(
                    title=title,
                    bullets=bullets,
                    referedUrls=referedUrls,
                    referredImages=referredImages
                ))
                
                _end = True

            elif line.startswith("-"):
                # add bullet
                if _start and not _end:
                    bullets.append(line[1:].strip(": "))

        return clusters
        

        