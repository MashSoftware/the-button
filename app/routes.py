from datetime import datetime

from app import app, db
from app.forms import (AccountForm, EventForm, LoginForm, PasswordForm,
                       SignupForm)
from app.models import Event, User
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.exceptions import Forbidden
from werkzeug.urls import url_parse


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
    return render_template('sign_up_form.html', title='Sign up', form=form)


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
    return render_template('log_in_form.html', title='Log in', form=form)


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


@app.route('/account/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.updated_at = datetime.utcnow()
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been changed', 'success')
        else:
            flash('Invalid password.', 'danger')
            return redirect(url_for('change_password'))
        return redirect(url_for('account'))

    return render_template('password_form.html', title='Change password', form=form)


@app.route('/account/update', methods=['GET', 'POST'])
@login_required
def update_account():
    form = AccountForm()
    if form.validate_on_submit():
        current_user.email_address = form.email_address.data
        current_user.updated_at = datetime.utcnow()
        db.session.add(current_user)
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.email_address.data = current_user.email_address
    return render_template('account_form.html', title='Update details', form=form)


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


@app.route('/push/<uuid:id>/delete')
@login_required
def delete_event(id):
    event = Event.query.get_or_404(str(id))
    if event not in current_user.events:
        raise Forbidden()
    db.session.delete(event)
    db.session.commit()
    flash('Time entry has been deleted', 'success')
    return redirect(url_for('index'))


@app.route('/push/<uuid:id>/update', methods=['GET', 'POST'])
@login_required
def update_event(id):
    event = Event.query.get_or_404(str(id))
    if event not in current_user.events:
        raise Forbidden()
    form = EventForm()
    if form.validate_on_submit():
        event.started_at = form.started_at.data
        event.ended_at = form.ended_at.data
        db.session.add(event)
        db.session.commit()
        flash('Time entry has been updated', 'success')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.started_at.data = event.started_at
        form.ended_at.data = event.ended_at
    return render_template('event_form.html', title='Edit time', form=form, event=event)
