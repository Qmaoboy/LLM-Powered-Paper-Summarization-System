from flask import Flask
import os,yaml
from lib.mysql_class import mysql_db_client

app = Flask(__name__)

@app.route('/')
def hello_world():
    host = os.getenv("DATABASE_HOST")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    database_name = os.getenv("DATABASE_NAME")

    with open('lib/config/config.yaml', 'r') as yamlfile:
        config = yaml.safe_load(yamlfile)
    client=mysql_db_client(config)

    return f"host={host}, user={user}, password={password}, database={database_name}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
