from datetime import datetime

import pytz
from app import db, limiter
from app.entry import bp
from app.entry.forms import EventForm
from app.models import Event
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden


@bp.route("/")
@login_required
@limiter.limit("1 per second", key_func=lambda: current_user.id)
def entries():
    page = request.args.get("page", 1, type=int)
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.desc()).paginate(page, 10, True)
    last_event = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.desc()).first()
    if (last_event and last_event.ended_at) or last_event is None:
        start = True
    else:
        start = False

    int_dict = {}
    for event in events.items:
        event.started_at = event.started_at.astimezone(pytz.timezone(current_user.timezone))
        if event.ended_at:
            event.ended_at = event.ended_at.astimezone(pytz.timezone(current_user.timezone))

        date_dict = int_dict.setdefault(
            event.started_at.strftime("%A %d %B %Y"),
            {"entries": [], "total_seconds": 0, "total_duration": None, "total_duration_decimal": 0},
        )
        date_dict["entries"].append(event)
        if event.ended_at:
            date_dict["total_seconds"] += event.duration()
            hours, remainder = divmod(date_dict["total_seconds"], 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                date_dict["total_duration"] = str(hours) + " h " + str(minutes) + "min"
            elif minutes > 0:
                date_dict["total_duration"] = str(minutes) + " min"
            else:
                date_dict["total_duration"] = str(seconds) + "s"
            date_dict["total_duration_decimal"] += event.duration_decimal()

    output = [
        {
            "date": key,
            "entries": value["entries"],
            "total_duration": value["total_duration"],
            "total_duration_decimal": value["total_duration_decimal"],
        }
        for key, value in int_dict.items()
    ]
    return render_template("entry/entries.html", events=events, start=start, entries=output)


@bp.route("/auto")
@login_required
@limiter.limit("1 per second", key_func=lambda: current_user.id)
def auto():
    event = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.desc()).first()
    if event and event.ended_at is None:
        event.ended_at = pytz.utc.localize(datetime.utcnow())
        db.session.add(event)
    else:
        if current_user.entry_limit <= len(current_user.events):
            oldest_event = Event.query.filter_by(user_id=current_user.id).order_by(Event.started_at.asc()).first()
            db.session.delete(oldest_event)
            flash(
                "You have reached the {0} entry limit for your account. The oldest entry has been deleted.".format(
                    current_user.entry_limit
                ),
                "warning",
            )
        event = Event(user_id=current_user.id, started_at=pytz.utc.localize(datetime.utcnow()))
        event.tag_id = request.args.get("tag_id", None, type=str)
        db.session.add(event)
    db.session.commit()
    return redirect(url_for("entry.entries"))


@bp.route("/manual", methods=["GET", "POST"])
@login_required
@limiter.limit("1 per second", key_func=lambda: current_user.id)
def manual():
    form = EventForm()
    form.tag.choices = [(tag.id, tag.name) for tag in current_user.tags]
    form.tag.choices.insert(0, ("None", "None"))
    if form.validate_on_submit():
        started_at = datetime(
            form.started_at_date.data.year,
            form.started_at_date.data.month,
            form.started_at_date.data.day,
            form.started_at_time.data.hour,
            form.started_at_time.data.minute,
            form.started_at_time.data.second,
        )
        locale_started_at = pytz.timezone(current_user.timezone).localize(started_at)
        utc_started_at = locale_started_at.astimezone(pytz.utc)
        event = Event(user_id=current_user.id, started_at=utc_started_at)
        if form.ended_at_date.data and form.ended_at_time.data:
            ended_at = datetime(
                form.ended_at_date.data.year,
                form.ended_at_date.data.month,
                form.ended_at_date.data.day,
                form.ended_at_time.data.hour,
                form.ended_at_time.data.minute,
                form.ended_at_time.data.second,
            )
            locale_ended_at = pytz.timezone(current_user.timezone).localize(ended_at)
            utc_ended_at = locale_ended_at.astimezone(pytz.utc)
            event.ended_at = utc_ended_at
        else:
            event.ended_at = None
        if form.tag.data != "None":
            event.tag_id = form.tag.data
        db.session.add(event)
        db.session.commit()
        flash("Time entry has been added.", "success")
        return redirect(url_for("entry.entries"))
    return render_template("entry/create_entry_form.html", title="Create time entry", form=form)


@bp.route("/<uuid:id>", methods=["GET", "POST"])
@login_required
@limiter.limit("1 per second", key_func=lambda: current_user.id)
def update(id):
    event = Event.query.get_or_404(str(id))
    if event not in current_user.events:
        raise Forbidden()
    form = EventForm()
    form.tag.choices = [(tag.id, tag.name) for tag in current_user.tags]
    form.tag.choices.insert(0, ("None", "None"))
    if form.validate_on_submit():
        started_at = datetime(
            form.started_at_date.data.year,
            form.started_at_date.data.month,
            form.started_at_date.data.day,
            form.started_at_time.data.hour,
            form.started_at_time.data.minute,
            form.started_at_time.data.second,
        )
        locale_started_at = pytz.timezone(current_user.timezone).localize(started_at)
        utc_started_at = locale_started_at.astimezone(pytz.utc)
        event.started_at = utc_started_at
        if form.ended_at_date.data and form.ended_at_time.data:
            ended_at = datetime(
                form.ended_at_date.data.year,
                form.ended_at_date.data.month,
                form.ended_at_date.data.day,
                form.ended_at_time.data.hour,
                form.ended_at_time.data.minute,
                form.ended_at_time.data.second,
            )
            locale_ended_at = pytz.timezone(current_user.timezone).localize(ended_at)
            utc_ended_at = locale_ended_at.astimezone(pytz.utc)
            event.ended_at = utc_ended_at
        else:
            event.ended_at = None
        if form.tag.data != "None":
            event.tag_id = form.tag.data
        else:
            event.tag_id = None
        db.session.add(event)
        db.session.commit()
        flash("Time entry has been updated.", "success")
        return redirect(url_for("entry.entries"))
    elif request.method == "GET":
        # Show timestamp in users localised timezone
        form.started_at_date.data = event.started_at.astimezone(pytz.timezone(current_user.timezone))
        form.started_at_time.data = event.started_at.astimezone(pytz.timezone(current_user.timezone))
        if event.ended_at:
            form.ended_at_date.data = event.ended_at.astimezone(pytz.timezone(current_user.timezone))
            form.ended_at_time.data = event.ended_at.astimezone(pytz.timezone(current_user.timezone))
        if event.tag_id:
            form.tag.data = event.tag_id
    return render_template("entry/update_entry_form.html", title="Edit time entry", form=form, event=event)


@bp.route("/<uuid:id>/delete")
@login_required
@limiter.limit("1 per second", key_func=lambda: current_user.id)
def delete(id):
    event = Event.query.get_or_404(str(id))
    if event not in current_user.events:
        raise Forbidden()
    db.session.delete(event)
    db.session.commit()
    flash("Time entry has been deleted.", "success")
    return redirect(url_for("entry.entries"))
