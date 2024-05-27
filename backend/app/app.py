from flask import Flask, render_template, request
import os
import yaml
import requests
from lib.mysql_class import mysql_db_client  # Ensure this custom module is correctly implemented
from lib.gpt_worker import GPT_Analysis_
from lib.mysql_class import sql_operater
import glob


app = Flask(__name__, template_folder='templates')
with open('lib/config/config.yaml', 'r') as yamlfile:
    config = yaml.safe_load(yamlfile)

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
    if function == 'summarize':
        task = request.form['task']
        if task == 'papers':
            path = os.getcwd() + "/" + request.form['folder_path']
            GPT_Analysis_(config, [path])
            return render_template("Text_page/summarize.html", path = path)
        elif task == 'news':
            return render_template("Text_page/test.html")
    elif function == 'database':
        task = request.form['db_task']
        sql = sql_operater(config)
        if task == 'search':
            folder_name = request.form['folder_name']
            keyword = request.form['keyword']
            sql.Search_by_keyword(folder_name, keyword)
            return render_template("Text_page/summarize.html")
        elif task == 'init':
            initial = request.form.get('initial')
            if initial == 'on':
                sql.Iniitalize_Sql_table()
                return render_template("Text_page/reset.html")
            else :
                return 'Please select the checkbox'
    elif function == 'test':
        test1 = request.form['test_param1']
        test2 = request.form['test_param2']
        return render_template("Text_page/test.html", test1=test1, test2=test2)
    else:
        return 'Invalid function'
if __name__ == "__main__":
    # Setting host to '0.0.0.0' allows the server to be accessible externally
    # Port 5000 is the default for Flask, explicitly stated here for clarity
    app.run(host='0.0.0.0', port=5000,debug=True)

