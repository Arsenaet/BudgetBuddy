"""Budget Buddy Flask application for managing personal budget items and expenditures."""

import logging
import re
from datetime import datetime

from flask import Flask, render_template, request, redirect, jsonify
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from markdown import markdown
from waitress import serve
from PerpLibs import Request, Textonly

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Item {self.id}>'



@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    """Display the main budget items page and handle item creation."""
    if request.method == 'POST':
        item_name = request.form['item']
        item_cost = request.form.get('cost', 0)  # Add default cost of 0 if not provided
        
        try:
            item_cost = int(item_cost)
            new_item = Todo(item=item_name, cost=item_cost)
            
            db.session.add(new_item)
            db.session.commit()
            return redirect('/')
        except sqlalchemy.exc.SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return 'There was an issue adding your item'
        except ValueError as e:
            app.logger.error("Value error: %s", e)
            return 'Invalid cost value'
    else:
        items = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', items=items)    


@app.route('/delete/<int:id>')
def delete(id):
    """Delete a budget item from the database by its ID."""
    item_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect('/')
    except sqlalchemy.exc.SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return 'There was a problem deleting that item'
    

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    """Update an existing budget item by its ID."""
    item = Todo.query.get_or_404(id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.cost = int(request.form.get('cost', 0))

        try:
            db.session.commit()
            return redirect('/')
        except sqlalchemy.exc.SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return 'There was an issue updating your item'

    else:
        return render_template('update.html', item=item)


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    app.logger.error("Server Error: %s", error)
    return "Internal Server Error", 500

@app.route("/submit", methods=["POST"])
def submit():
    """Process queries using Perplexity API and return results."""
    try:
        # Retrieve the input from the JSON body
        user_query = request.json.get("userQuery")
        if not user_query:
            return jsonify({'prompt_result': 'Please provide a query'}), 400
            
        restrictions = "Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not type a response to these requirements"
        user_query += restrictions
        
        # Process the query using Perplexity API
        try:
            response = Request(user_query)
            prompt_result = Textonly(response)  # Extract text from API response
            prompt_result = re.sub(r'\[\d+\]', '', prompt_result)
            
            # Convert markdown to HTML
            html_result = markdown(prompt_result)
            return jsonify({'prompt_result': html_result})
        except Exception as e:
            app.logger.error("Perplexity API error: %s", e)
            return jsonify({'prompt_result': f"Error connecting to AI service: {str(e)}"}), 500

    except Exception as e:
        app.logger.error("Request processing error: %s", e)
        return jsonify({'prompt_result': f"Error processing request: {str(e)}"}), 500

# Create database tables
with app.app_context():
    db.create_all()
    app.logger.info("Database tables created")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    serve(app, host="0.0.0.0", port=8000)
