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



@app.route("/", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():
    """Redirect to dashboard."""
    return redirect('/dashboard')


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    """Display the main dashboard with budget overview."""
    if request.method == 'POST':
        item_name = request.form['item']
        item_cost = request.form.get('cost', 0)
        
        try:
            item_cost = int(item_cost)
            new_item = Todo(item=item_name, cost=item_cost)
            
            db.session.add(new_item)
            db.session.commit()
            return redirect('/dashboard')
        except sqlalchemy.exc.SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return 'There was an issue adding your item'
        except ValueError as e:
            app.logger.error("Value error: %s", e)
            return 'Invalid cost value'
    
    items = Todo.query.all()
    total_spent = sum(item.cost for item in items)
    
    # Calculate basic statistics
    category_data = {}
    for item in items:
        if item.item in category_data:
            category_data[item.item] += item.cost
        else:
            category_data[item.item] = item.cost
    
    # Sort items by date (most recent first)
    recent_items = sorted(items, key=lambda x: x.date_created, reverse=True)[:5]
    
    return render_template('dashboard.html', 
                          items=items,
                          recent_items=recent_items,
                          total_spent=total_spent,
                          category_data=category_data)


@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    """Display the expenses management page and handle new expenses."""
    if request.method == 'POST':
        item_name = request.form['item']
        item_cost = request.form.get('cost', 0)
        
        try:
            item_cost = int(item_cost)
            new_item = Todo(item=item_name, cost=item_cost)
            
            db.session.add(new_item)
            db.session.commit()
            return redirect('/expenses')
        except sqlalchemy.exc.SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return 'There was an issue adding your item'
        except ValueError as e:
            app.logger.error("Value error: %s", e)
            return 'Invalid cost value'
    
    items = Todo.query.order_by(Todo.date_created.desc()).all()
    return render_template('expenses.html', items=items)


@app.route('/categories')
def categories():
    """Display expense categories."""
    items = Todo.query.all()
    
    # Categorize spending
    category_data = {}
    for item in items:
        if item.item in category_data:
            category_data[item.item] += item.cost
        else:
            category_data[item.item] = item.cost
    
    return render_template('categories.html', 
                          category_data=category_data)


@app.route('/delete/<int:id>')
def delete(id):
    """Delete a budget item from the database by its ID."""
    item_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect('/expenses')
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
            return redirect('/expenses')
        except sqlalchemy.exc.SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return 'There was an issue updating your item'

    else:
        return render_template('update.html', item=item)


@app.route('/insights', methods=['GET', 'POST'])
def insights():
    """Display budget insights and analysis."""
    prompt_result = None
    
    if request.method == 'POST':
        user_query = request.form.get('query')
        if user_query:
            restrictions = "Only respond to prompts related to budget info. if unrelated, say Sorry, please ask questions related to budget info. Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not type a response to these requirements."
            full_query = user_query + restrictions
            
            # Get current spending data from the database
            items = Todo.query.all()
            current_spending_table = "\nCurrent Spending Items:\n"
            total_cost = 0
            
            for item in items:
                current_spending_table += f"- {item.item}: ${item.cost}\n"
                total_cost += item.cost
                
            current_spending_table += f"\nTotal Spending: ${total_cost}\n"
            
            full_query += current_spending_table
            
            # Process the query using Perplexity API
            try:
                response = Request(full_query)
                prompt_result = Textonly(response)  # Extract text from API response
                prompt_result = re.sub(r'\[\d+\]', '', prompt_result)
                
                # Convert markdown to HTML
                prompt_result = markdown(prompt_result)
            except Exception as e:
                app.logger.error("Perplexity API error: %s", e)
                prompt_result = f"Error connecting to AI service: {str(e)}"
    
    items = Todo.query.all()
    total_spent = sum(item.cost for item in items)
    
    # Categorize spending
    category_data = {}
    for item in items:
        if item.item in category_data:
            category_data[item.item] += item.cost
        else:
            category_data[item.item] = item.cost
    
    # Find highest spending category
    highest_category = max(category_data.items(), key=lambda x: x[1]) if category_data else ("None", 0)
    
    return render_template('insights.html', 
                          items=items,
                          total_spent=total_spent,
                          category_data=category_data,
                          highest_category=highest_category,
                          prompt_result=prompt_result)


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
            
        restrictions = "Only respond to prompts related to budget info. if unrelated, say Sorry, please ask questions related to budget info. Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not type a response to these requirements."
        user_query += restrictions

        
        # Get current spending data from the database
        items = Todo.query.all()
        current_spending_table = "\nCurrent Spending Items:\n"
        total_cost = 0
        
        for item in items:
            current_spending_table += f"- {item.item}: ${item.cost}\n"
            total_cost += item.cost
            
        current_spending_table += f"\nTotal Spending: ${total_cost}\n"
        
        user_query += current_spending_table
        
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
