from flask import Flask, render_template, request
import logging
import os
from PerpLibs import Request
from waitress import serve

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
    user_query = request.form.get("userQuery")  # Retrieve the input from the form
    try:
        # Process the query using Perplexity API
        response = Request(user_query)
        prompt_result = (response)  # Extract text from API response
        print(prompt_result)
        print(response["choices"][0]["message"]["content"])
    except Exception as e:
        prompt_result = f"Error: {str(e)}"  # Handle errors gracefully

    # Render the index page with the result
    return render_template("index.html", promptresult=prompt_result["choices"][0]["message"]["content"])


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    serve(app, host="0.0.0.0", port=8000)
