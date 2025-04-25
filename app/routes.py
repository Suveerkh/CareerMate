from flask import render_template, request, redirect, url_for, flash
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import create_user, get_user_by_email


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='sha256')

        # Create the user in Supabase
        response = create_user(username, email, hashed_password)

        if response.status_code == 201:
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error creating account: ' + str(response), 'danger')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Retrieve user by email from Supabase
        user = get_user_by_email(email)

        if user and check_password_hash(user[0]['password_hash'], password):
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')
