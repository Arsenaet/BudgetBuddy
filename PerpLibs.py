from dotenv import load_dotenv
import requests
import os
import logging

load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.DEBUG)

def Request(query):
    '''
    Takes in a request as a string, outputs full JSON
    '''
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
                "content": f"{query}"
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
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json"
    }

    try:
        # Log the request being made
        logging.debug(f"Making request to Perplexity API with query: {query}")
        response = requests.request("POST", url, json=payload, headers=headers)

        # Check if the response is valid
        if response.status_code != 200:
            logging.error(f"API Error: {response.status_code} - {response.text}")
            return {"error": "API Error, please try again later"}, 500

        return response.json()

    except Exception as e:
        logging.error(f"Error while making request: {str(e)}")
        return {"error": str(e)}, 500
