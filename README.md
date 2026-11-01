# NeuroPrompt - Simple Plain HTML + Flask + MySQL

This version keeps the functionality of the uploaded NeuroPrompt page but uses normal HTML files instead of Jinja templates.

## Pages
- login.html - authentication
- languages.html - Python, C++, C and Java cards
- library.html - save/load prompt templates
- analyzer.html - code diagnostic check
- history.html - database-backed analysis history

## Setup
1. Install Python.
2. Open this folder in VS Code.
3. Start XAMPP and start MySQL.
4. Open phpMyAdmin and import `database.sql`.
5. In PowerShell run:
   `python -m pip install -r requirements.txt`
6. Run:
   `python app.py`
7. Open `http://127.0.0.1:5000/`

No Jinja syntax is used. Flask only serves the HTML files and provides API endpoints. JavaScript uses `fetch()` to communicate with Flask.
