import sqlite3
from flask import Flask, redirect, url_for, request, render_template, flash, redirect, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = '92051f34a4e348cd1311488984333c199abe2e57cc1fa4bf'

class AccountData(object):
    user_id = ""
    logged = False

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/menu')
def menu():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT name FROM users WHERE user_id = ?", (AccountData.user_id,)).fetchone()

    cur.close()
    con.close()

    return render_template("menu.html", name = result[0])


@app.route('/view')
def view():
    # for viewing existing listings
    return render_template('view.html')


@app.route('/add')
def add():
    # for adding a new listing
    return render_template('add.html')


@app.route('/edit')
def edit():
    # for adding email or changing username/password
    return render_template('edit.html')


@app.post('/confirm_credentials')
def confirm_credentials():
    username = request.form["l_username"]
    password = request.form["l_password"]

    if (username == ""):
        flash("Please enter a username.")
        return redirect("/")
    if (password == ""):
        flash("Please enter a password.")
        return redirect("/")

    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT user_id FROM users WHERE name = ? AND password = ?", (username, password)).fetchone()

    cur.close()
    con.close()

    if result != None:
        AccountData.user_id = str(result[0])
        return menu()
    else:
        flash("Login invalid.")
        return redirect("/")


@app.post('/create_user')
def create_user():
    username = request.form["c_username"]
    password = request.form["c_password"]
    
    if (username == ""):
        flash("Username cannot be empty.")
        return redirect("/")
    if (password == ""):
        flash("Password cannot be empty.")
        return redirect("/")
    
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT name FROM users WHERE name = ?", (username,)).fetchone()
    if (result is not None):
        flash("Username already exists. Please try another.")
        return redirect("/")
    
    # cur.execute("INSERT INTO users(name, password) VALUES(?, ?)", (username, password))

    result = cur.execute("SELECT user_id FROM users WHERE name = ? AND password = ?", (username, password)).fetchone()

    cur.close()
    con.close()

    if result != None:
        AccountData.user_id = str(result[0])
        return menu()
    else:
        flash("Login invalid.")
        return redirect("/")


if __name__ == "__main__":
    app.run()
