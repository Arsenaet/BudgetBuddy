from flask import Flask, render_template, request, jsonify
import logging
from PerpLibs import Request, Textonly
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
    try:
        # Retrieve the input from the JSON body
        user_query = request.json.get("userQuery")
        # Process the query using Perplexity API
        response = Request(user_query)
        prompt_result = Textonly(response)  # Extract text from API response
        print(prompt_result)
        print(response["choices"][0]["message"]["content"])
    except Exception as e:
        prompt_result = f"Error: {str(e)}"  # Handle errors gracefully

    # Return the result as JSON
    return jsonify({'prompt_result': prompt_result})

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    serve(app, host="0.0.0.0", port=8000)
