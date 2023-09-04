from flask import Flask
from dotenv import load_dotenv
import main

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)


@app.route('/welcome')
def welcome():
    return 'welcome'


@app.route('/search/<search_text>')
def search(search_text):
    return main.search(search_text)


if __name__ == '__main__':
    app.run()
