from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, SignupForm
from app.models import Event, User


@app.route('/')
def index():
    if current_user.is_authenticated:
        events = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.desc()).all()
        return render_template('index.html', events=events)
    else:
        return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            email_address=form.email_address.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for signing up! Please log in to continue.', 'success')
        return redirect(url_for('login'))
    return render_template('sign_up.html', title='Sign up', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email_address=form.email_address.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email address or password.', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        user.login_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        flash('Welcome back.', 'success')
        return redirect(next_page)
    return render_template('log_in.html', title='Log in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    return render_template('account.html', title='My Account')


@app.route('/account/delete')
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    flash('Your account and all personal information has been permanently deleted', 'success')
    return redirect(url_for('index'))


@app.route('/push')
@login_required
def create_event():
    event = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.desc()).first()
    if event and event.ended_at is None:
        event.ended_at = datetime.utcnow()
        db.session.add(event)
    else:
        new_event = Event(
            user_id=current_user.id,
            started_at=datetime.utcnow())
        db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('index'))
