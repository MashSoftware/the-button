from flask import flash, redirect, render_template, url_for

from app import app
from app.forms import LoginForm, SignupForm


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        flash('Thanks for signing up {}!'.format(form.first_name.data.title()), 'success')
        return redirect(url_for('index'))
    return render_template('sign_up.html', title='Sign up', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Welcome back', 'success')
        return redirect(url_for('index'))
    return render_template('log_in.html', title='Log in', form=form)
