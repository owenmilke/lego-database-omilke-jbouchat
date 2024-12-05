import sqlite3
from flask import Flask, redirect, url_for, request, render_template, flash, redirect, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = '92051f34a4e348cd1311488984333c199abe2e57cc1fa4bf'


@app.route('/')
def index():
    return render_template('login.html')