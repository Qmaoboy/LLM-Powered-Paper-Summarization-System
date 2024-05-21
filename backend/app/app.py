from flask import Flask, render_template, request
import os
import yaml
import requests
from lib.mysql_class import mysql_db_client  # Ensure this custom module is correctly implemented

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    # Retrieve environment variables
    host = os.getenv("DATABASE_HOST")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    database_name = os.getenv("DATABASE_NAME")
    # Correct the file path for Windows and potential deployment environments

    # Return the rendered HTML page
    return render_template("Text_page/front_page.html")

@app.route('/submit', methods=['POST'])
def submit():
    function = request.form['function']
    textinput = request.form['textinput']
    if function == 'summarize':
        # Here you would call a summarization function on textinput
        # summary = "This is where the summary would appear."
        return f"Input Text: {textinput} , Sorry the function is not implemented yet."
    elif function == 'analyze':
        return "Function not implemented."
    elif function == 'review':
        return "Function not implemented."

if __name__ == "__main__":
    # Setting host to '0.0.0.0' allows the server to be accessible externally
    # Port 5000 is the default for Flask, explicitly stated here for clarity
    app.run(host='0.0.0.0', port=5000,debug=True)

