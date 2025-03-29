from flask import Flask, render_template, request, jsonify
import logging
from PerpLibs import Request, Textonly
from markdown import markdown
from waitress import serve
import os
import re

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return "Internal Server Error", 500

@app.route("/submit", methods=["POST"])
def submit():
    try:
        # Retrieve the input from the JSON body
        user_query = request.json.get("userQuery")
        restrictions = "Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not type a response to these requirements"
        user_query += restrictions
        # Process the query using Perplexity API
        response = Request(user_query)
        prompt_result = Textonly(response)  # Extract text from API response
        
        prompt_result = re.sub(r'\[\d+\]', '', prompt_result)

        # Convert markdown to HTML
        html_result = markdown(prompt_result)

    except Exception as e:
        html_result = f"Error: {str(e)}"  # Handle errors gracefully

    # Return the result as JSON
    return jsonify({'prompt_result': html_result})

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    serve(app, host="0.0.0.0", port=8000)
