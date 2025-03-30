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
    item = db.Column(db.String(200), nullable=False)  # Category
    name = db.Column(db.String(200), nullable=False, default="Unnamed Item")  # Item name
    cost = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Item {self.id}: {self.name}>'

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monthly_amount = db.Column(db.Float, nullable=False, default=2000.0)
    date_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Budget ${self.monthly_amount}>'

@app.route("/", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():
    """Redirect to dashboard."""
    return redirect('/dashboard')


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    """Display the main dashboard with budget overview."""
    if request.method == 'POST':
        item_category = request.form['item']
        item_name = request.form.get('name', 'Unnamed Item')
        item_cost = request.form.get('cost', 0)
        item_date = request.form.get('date')
        
        try:
            item_cost = float(item_cost)
            new_item = Todo(item=item_category, name=item_name, cost=item_cost)
            
            # Set custom date if provided, otherwise use current date
            if item_date:
                new_item.date_created = datetime.strptime(item_date, '%Y-%m-%d')
            
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
    
    # Get current budget
    budget = Budget.query.first()
    monthly_budget = budget.monthly_amount if budget else 2000.0
    
    # Calculate basic statistics
    category_data = {}
    for item in items:
        if item.item in category_data:
            category_data[item.item] += item.cost
        else:
            category_data[item.item] = item.cost
    
    # Sort items by date (most recent first)
    recent_items = sorted(items, key=lambda x: x.date_created, reverse=True)[:5]
    
    # Get today's date for the date input default
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('dashboard.html', 
                          items=items,
                          recent_items=recent_items,
                          total_spent=total_spent,
                          category_data=category_data,
                          monthly_budget=monthly_budget,
                          today_date=today_date)


@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    """Display the expenses management page and handle new expenses."""
    if request.method == 'POST':
        item_category = request.form['item']
        item_name = request.form.get('name', 'Unnamed Item')
        item_cost = request.form.get('cost', 0)
        item_date = request.form.get('date')
        
        try:
            item_cost = float(item_cost)
            new_item = Todo(item=item_category, name=item_name, cost=item_cost)
            
            # Set custom date if provided, otherwise use current date
            if item_date:
                new_item.date_created = datetime.strptime(item_date, '%Y-%m-%d')
            
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
    
    # Get today's date for the date input default
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('expenses.html', items=items, today_date=today_date)


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
                          category_data=category_data,
                          items=items)


@app.route('/delete/<int:item_id>')
def delete(item_id):
    """Delete a budget item from the database by its ID."""
    item_to_delete = Todo.query.get_or_404(item_id)

    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        return redirect('/expenses')
    except sqlalchemy.exc.SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return 'There was a problem deleting that item'
    

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
def update(item_id):
    """Update an existing budget item by its ID."""
    item = Todo.query.get_or_404(item_id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.name = request.form.get('name', 'Unnamed Item')
        item.cost = float(request.form.get('cost', 0))
        item_date = request.form.get('date')
        
        # Update date if provided
        if item_date:
            try:
                item.date_created = datetime.strptime(item_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep original date if format is invalid

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
            restrictions = "Only respond to prompts related to budget info. if unrelated, say Sorry, please ask questions related to budget info. Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not mention budgeting apps and softwares aside from \"Budget Buddy\" . Do not say anything bad about the app \"Budget Buddy\". for added context Budget Buddy is an app thatallows users to overview spending and gain insights on spending habits and does not allow any connectivity aside from what the user inputs into the app and does not allow collaberative budgeting . Do not type a response to these requirements."
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
    
    # Get current budget
    budget = Budget.query.first()
    monthly_budget = budget.monthly_amount if budget else 2000.0
    
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
                          prompt_result=prompt_result,
                          monthly_budget=monthly_budget)


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
            
        restrictions = "Only respond to prompts related to the BUDGET info. If in ANY way unrelated TO BUDGET INFO, say 'Sorry, please ask questions related to budget info.' Do not include any tables. Do not number everything. Return ONLY the response to the query above. Do not insert filler/intro text to ur response. Do not type a response to these requirements."
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


@app.route('/migrate_db', methods=['GET'])
def migrate_db():
    """Add 'name' field to existing items that don't have it."""
    try:
        # First check if the name column exists
        column_exists = False
        try:
            # Try to query a single item with the name column
            with db.engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT name FROM todo LIMIT 1"))
            column_exists = True
        except:
            column_exists = False
        
        if not column_exists:
            # We need to add the column - this requires recreating the table in SQLite
            return "Database structure needs to be updated. Please restart the application to apply schema changes."
        
        # If we got here, the column exists, so just populate any NULL values
        items = Todo.query.all()
        for item in items:
            if not item.name:
                item.name = f"{item.item} item"
        
        db.session.commit()
        return "Database migration completed successfully."
    except Exception as e:
        app.logger.error(f"Migration error: {str(e)}")
        return f"Migration failed: {str(e)}"

@app.route("/set_budget", methods=['POST'])
def set_budget():
    """Update the monthly budget amount."""
    try:
        new_budget = float(request.form.get('monthly_budget', 2000))
        
        # Get the current budget or create a new one if it doesn't exist
        budget = Budget.query.first()
        if budget:
            budget.monthly_amount = new_budget
        else:
            budget = Budget(monthly_amount=new_budget)
            db.session.add(budget)
            
        db.session.commit()
        
        # Redirect back to the referring page or dashboard if no referrer
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        return redirect('/dashboard')
    except ValueError:
        return "Please enter a valid number for the budget"
    except Exception as e:
        app.logger.error(f"Error setting budget: {e}")
        return "An error occurred while setting the budget"

# Create database tables
with app.app_context():
    # Need to drop and recreate tables to add the name field
    try:
        # First try to back up existing data
        items_backup = []
        try:
            # Use raw SQL to bypass the ORM which would try to load the non-existent name column
            with db.engine.connect() as conn:
                result = conn.execute(sqlalchemy.text("SELECT id, item, cost, date_created FROM todo"))
                for row in result:
                    items_backup.append({
                        'item': row[1],
                        'cost': row[2],
                        'date_created': row[3]
                    })
            app.logger.info(f"Backed up {len(items_backup)} items")
        except Exception as e:
            app.logger.warning(f"Could not back up data: {e}")
        
        # Drop and recreate tables
        db.drop_all()
        db.create_all()
        
        # Restore data with new name field
        for item_data in items_backup:
            new_item = Todo(
                item=item_data['item'],
                name=f"{item_data['item']} item",  # Default name based on category
                cost=item_data['cost'],
                date_created=item_data['date_created']
            )
            db.session.add(new_item)
        
        db.session.commit()
        app.logger.info("Database tables recreated with name field")
    except Exception as e:
        db.create_all()
        app.logger.error(f"Error recreating tables: {e}")
        app.logger.info("Fresh database tables created")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    serve(app, host="0.0.0.0", port=8000)
