import os
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)


@app.route('/')
def index():
    return


@app.route('/api/report', methods=['GET', 'POST'])
def generate_reports():
    args = ['python', 'reportgenerator.py']
    subprocess.call(args)


if __name__ == '__main__':
    app.run()
