import os
import json
import time
import torch

from utils import NewsSearchHelper
from dotenv import load_dotenv
from models import NewsSearchResult


from sklearn.cluster import KMeans

from transformers import BertModel, BertTokenizer
model_name = 'bert-base-uncased'

# get script file path
path = './data'
env_file = ".env.local"
load_dotenv(env_file)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_URL = os.getenv("NEWSAPI_URL")
newsSearchHelper = NewsSearchHelper(NEWSAPI_URL, NEWSAPI_KEY)

# path.join file path and hot_queries.txt
def norm_query():
    qs = set()
    with open(os.path.join(path, './hot_queries.txt'), 'r') as f:
        for line in f:
            line = line.strip('\n ')
            q = line.lower()
            qs.add(q)

    with open(os.path.join(path, './hot_queries_norm.txt'), 'w') as f:
        qs = sorted(list(qs))
        for q in qs:
            f.write(q + '\n')

def scrape_bingnews(qs):
    res = []
    json_output = "./hot_queries_news_search_res.json"
    for i, q in enumerate(qs):
        try:
            news_res = newsSearchHelper.search(q, 'en-us', 20)
            d = {"news_search": [item.dict() for item in news_res], "query": q, "crawl_time": int(time.time())}
            res.append(d)
            print(i, q, len(news_res))
            print("Sleeping...1secs")
            time.sleep(1)
        except:
            print(f"Error! Skip {i}, {q}")
    json.dump(res, open(os.path.join(path, json_output), 'w'))

def clustering_news():
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    
    json_output = "./hot_queries_news_search_res.json"
    res = json.load(open(os.path.join(path, json_output), 'r'))
    for i, item in enumerate(res):
        print(i, item['query'])
        news =[NewsSearchResult(**sub_item) for sub_item in item['news_search']]
        print(len(news))

        texts = [sub_item.title for sub_item in news]

        #print([len(text.split()) for text in texts])
        input_ids = tokenizer(texts, padding=True, return_tensors='pt').input_ids
        #print([len(text) for text in input_ids])
        print(input_ids.shape)
        #print(input_ids)
        

        last_hidden_states = model(input_ids)[0] # Models outputs are now tuples
        sentence_embs = last_hidden_states[:, 0, :].detach().numpy()

        num_clusters = 5
        clustering_model = KMeans(n_clusters=num_clusters)
        clustering_model.fit(sentence_embs)
        cluster_assignment = clustering_model.labels_

        clustered_sentences = [[] for i in range(num_clusters)]
        for sentence_id, cluster_id in enumerate(cluster_assignment):
            clustered_sentences[cluster_id].append(texts[sentence_id])
        for sub in  clustered_sentences:
            print("\n##Start")
            print("\n".join(sub))
            print("##End\n")
        
        break;

if __name__ == "__main__":
    clustering_news()
        # get embeddings for news