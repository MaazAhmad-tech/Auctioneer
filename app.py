import sqlite3
from flask import flash, Flask, render_template, url_for, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import *
import os

UPLOAD_FOLDER = 'static/photos/'

app = Flask(__name__)
app.secret_key = "a2g2"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SESSION_PERMANENT"] = False
app.config["ENV"] = "development"
app.config["DEBUG"] = True
app.config["TESTING"] = True


@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("index.html")
    return redirect("/user")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", error=0)
    else:
        with sqlite3.connect("Data.db") as connection:
            connection.row_factory = sqlite3.Row
            db = connection.cursor()
            fname = request.form.get("first-name")
            lname = request.form.get("last-name")
            email = request.form.get("email")
            email = email.lower()
            row = db.execute(
                "SELECT * FROM users WHERE email = :email", {"email": email}).fetchall()
            if len(row) != 0:
                return render_template("signup.html", error="Email Id Already Registered")
            gender = request.form.get("gender")
            pswd = generate_password_hash(request.form.get("psw"))
            db.execute("INSERT INTO users (fname, lname, email, gender, hashpass) VALUES (:fname, :lname, :email, :gender, :hashpass)", {
                       "fname": fname, "lname": lname, "email": email, "gender": gender, "hashpass": pswd})
            connection.commit()
        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" not in session:
        if request.method == "GET":
            return render_template("login.html", error=0)
        with sqlite3.connect("Data.db") as connection:
            connection.row_factory = sqlite3.Row
            db = connection.cursor()
            email = request.form.get("email")
            email = email.lower()
            pswd = request.form.get("psw")
            row = db.execute(
                "SELECT * FROM users where email = :email", {"email": email}).fetchall()
            if len(row) != 1 or not(check_password_hash(row[0]["hashpass"], pswd)):
                return render_template("login.html", error="Invalid Email Id/Password")
            session["user_id"] = row[0]["id"]
    return redirect("/user")


@app.route("/user", methods=["GET", "POST"])
def user():
    if "user_id" in session:
        if request.method == "GET":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                id = session["user_id"]
                row = db.execute(
                    "SELECT * FROM users WHERE id = :id", {"id": id}).fetchall()
                items = db.execute(
                    "SELECT * FROM items").fetchall()
                return render_template("afterlogin.html", name=row[0]["fname"], items=items)
        elif request.method == "POST":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                search = request.form.get("search")
                items = db.execute(
                    "SELECT * FROM items WHERE item_name LIKE ?", ('%'+search+'%',)).fetchall()
                if len(items) >= 1:
                    item_id = items[0]['id']
                    return redirect(url_for("viewitem", item_id=item_id))
    return redirect("/login")


@app.route("/user/<category>")
def category(category):
    if "user_id" in session:
        with sqlite3.connect("Data.db") as connection:
            connection.row_factory = sqlite3.Row
            db = connection.cursor()
            id = session["user_id"]
            row = db.execute(
                "SELECT * FROM users WHERE id = :id", {"id": id}).fetchall()
            items = db.execute(
                "SELECT * FROM items WHERE category = :category", {"category": category}).fetchall()
            return render_template("afterlogin.html", name=row[0]["fname"], items=items)
    return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
def sell():
    if "user_id" in session:
        if request.method == "GET":
            return render_template("sell.html")
        elif request.method == "POST":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                user = session["user_id"]
                item_name = request.form.get("product")
                category = request.form.get("category")
                price = request.form.get("price")
                item_desc = request.form.get("desc")
                expiry = request.form.get("time")
                file = request.files["photo"]
                imagesrc = file.filename
                if imagesrc == '':
                    return redirect(request.url)
                filename = secure_filename(file.filename)
                file.save(os.path.join(
                    app.config["UPLOAD_FOLDER"], filename))
                db.execute("INSERT INTO items (user, category, item_name, imagesrc, price, expiry, item_desc) VALUES (:user, :category, :item_name, :imagesrc, :price, :expiry, :item_desc)", {
                           "user": user, "category": category, "item_name": item_name, "imagesrc": imagesrc, "price": price, "expiry": expiry, "item_desc": item_desc})
                return redirect("/user")
    return redirect("/login")


@app.route("/user/<int:item_id>", methods=["GET", "POST"])
def viewitem(item_id):
    if "user_id" in session:
        if request.method == "GET":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                id = session["user_id"]
                item = db.execute(
                    "SELECT * FROM items WHERE id = :id", {"id": item_id}).fetchall()
                seller = db.execute(
                    "SELECT * FROM users WHERE id = :id", {"id": item[0]["user"]}).fetchall()
                bidder = db.execute(
                    "SELECT * FROM users WHERE id = :id", {"id": item[0]["curr_bidder"]}).fetchall()
                if len(bidder) < 1:
                    bidder = -1
                return render_template("itemdesc.html", item=item, seller=seller, bidder=bidder)
        elif request.method == "POST":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                bid = request.form.get("currbid")
                bidder = db.execute(
                    "SELECT * FROM items where id = :id", {"id": item_id}).fetchall()
                if bidder[0]['user'] == session["user_id"]:
                    return redirect("/user")
                db.execute("UPDATE items SET curr_bidder = :bid WHERE id = :id",
                           {"bid": session["user_id"], "id": item_id})
                db.execute("UPDATE items SET price = :price WHERE id = :id",
                           {"price": bid, "id": item_id})
                return redirect("/user")
    return redirect("/login")


@app.route("/transaction")
def trans():
    if "user_id" in session:
        with sqlite3.connect("Data.db") as connection:
            connection.row_factory = sqlite3.Row
            db = connection.cursor()
            sold = db.execute(
                "SELECT * FROM items WHERE user = :user", {"user": session["user_id"]}).fetchall()
            bought = db.execute(
                "SELECT * FROM items WHERE curr_bidder= :curr", {"curr": session["user_id"]}).fetchall()
            return render_template("transaction.html", sold=sold, bought=bought)
    return redirect("/login")


@app.route("/about")
def aboutus():
    return render_template("about.html")


@app.route("/profile", methods=["GET", "POST"])
def profilee():
    if "user_id" in session:
        if request.method == "GET":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                username = db.execute(
                    "SELECT * FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()
                return render_template("profile.html", username=username)
        if request.method == "POST":
            with sqlite3.connect("Data.db") as connection:
                connection.row_factory = sqlite3.Row
                db = connection.cursor()
                fname = request.form.get("fname")
                lname = request.form.get("lname")
                pswd = generate_password_hash(request.form.get("cpsswd"))
                db.execute("UPDATE users SET fname = :fname, lname = :lname, hashpass = :pass WHERE id = :id", {
                           "fname": fname, "lname": lname, "pass": pswd, "id": session["user_id"]})
    return redirect("/login")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")
