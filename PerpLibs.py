from dotenv import load_dotenv
from pprint import pprint
import requests
import os

load_dotenv()
def PostRequest():
    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "How many stars are there in our galaxy?"
            }
        ],
        "max_tokens": 123,
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "web_search_options": {"search_context_size": "high"}
    }
    headers = {
        "Authorization": f"Bearer {os.getenv("PERPLEXITY_API_KEY")}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()

    #see docs for parsing usage
    print(response)
    print(response["choices"][0]["message"]["content"])

PostRequest()



