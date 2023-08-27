from flask import Flask
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

app = Flask(__name__)


@app.route('/welcome')
def welcome():
    return 'welcome'


if __name__ == '__main__':
    app.run()
