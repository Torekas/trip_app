from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from .forms import RegistrationForm, LoginForm
from auth.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users = current_app.users_col
        if users.find_one({"username": form.username.data}):
            flash("Username already taken", "danger")
        else:
            hashed = generate_password_hash(form.password.data)
            result = users.insert_one({"username": form.username.data, "password": hashed})
            user = User(str(result.inserted_id), form.username.data)
            login_user(user)
            flash("Registration successful", "success")
            return redirect(url_for("items.list_items"))
    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = current_app.users_col
        doc = users.find_one({"username": form.username.data})
        if doc and check_password_hash(doc["password"], form.password.data):
            user = User(str(doc["_id"]), doc["username"])
            login_user(user)
            flash("Logged in successfully", "success")
            next_page = request.args.get("next") or url_for("items.list_items")
            return redirect(next_page)
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("auth.login"))
