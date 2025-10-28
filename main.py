from openai import OpenAI
from webscraper import crawl_headings_with_text
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import os
load_dotenv()


api_keys = os.getenv("OPENAI_API_KEY")


client_open = OpenAI(api_key=api_keys)


data = crawl_headings_with_text("https://ku.edu.np/")  

def get_embedding(text):
    response = client_open.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

for item in data:
    item['embedding'] = get_embedding(item['heading'])
    

client = chromadb.PersistentClient(path="./db")  
collection = client.get_or_create_collection("website_headings")

for i, item in enumerate(data):
    collection.add(
        documents=[item['heading']],              
        metadatas=[{
            "url": item['url'],
            "text": item['longest_paragraph']
        }],         
        ids=[str(i)],
        embeddings=[item['embedding']]            
    )
    
query = "Result of Undergraduate"
query_emb = get_embedding(query)

results = collection.query(
    query_embeddings=[query_emb],
    n_results=1,
    include=['metadatas', 'documents']
)

print("Heading:", results['documents'][0][0])
print("URL:", results['metadatas'][0][0]['url'])
print("Text:", results['metadatas'][0][0].get('text'))

