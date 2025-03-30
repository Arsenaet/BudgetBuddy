![Alt text](readmeimages/BudgetBuddyLogo.png)

# Budget Buddy!
*Your buddy for budgeting*

This is the Readme! There isn't much content here we **Budgeted** all of our time to make a good app

## Features
### Dashboard
*All you need at a glance*
image

Tired of page after page to use the most basic features of a product? Our dashboard is compact and convenient, providing fast and easy insights, metrics and pretty visuals you want to see including unique, bite sized AI powered tips! 

### Expenses
image

Whether you're feeling nostaligic for spreadheets of old, or you need some more controls (probably cause you punched in 4000 instead of 40.00, lets be real), the expenses tab has got you covered, giving you a nice, neat, no-nonsense of what you've spent your hard earned cash and what you want to add to make your insights more powerful

### Insights
image here

If you like pretty graphs, youre gonna love the insights page! This page is dedicated to giving you the most comprehensive overview of your finances as well as how you spend your money as well as powerful tools to help you better spend your money

image here

When it comes to cruncing knowledge, there's nothing better than leverageng the best number-crunching research finding inventions there is out there. Powered by perplexity's sonar AI, this AI will answer your questions one by one while taking into account all the data that you've provided BudgetBuddy to crunch the number so you dont have to, giving you some of the most well reaserched insights possible.

### Categories


## Instalation
this is gonna be step by step build instructons, if you have any technical knowlage, everything SHOULD be understanadble cause of the requirements, you also need a .env with a perplexity API key and secretkey (PERPLEXITY_API_KEY and ServerSecret)
###Requirements

**A couple of these are from testing, so arent used but are still on the install list because I dont care**

literally just run these terminal commands and you're set (these are on a unix based system, if you run windows sorry, just use linux bro, its so worth it)
```
git clone https://github.com/Arsenaet/BudgetBuddy
cd BudgetBuddy
pip install -r requirements.txt
pip install sqlalchemy flask_sqlalchemy (was messed up in build requirements lol)
make your .env file with your secrets and API keys as outlined above using your text editor of choice (hopefully neovim)
flask run -h app.py
```
Easy as that, your server is deplopyed, all you gotta do now is go to your web browser of choice and open localhost to port 8000 
