from datetime import datetime

import pytz
from app import db, limiter
from app.models import Event, Tag
from app.tag import bp
from app.tag.forms import TagForm
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.utils import seconds_to_decimal, seconds_to_string
from werkzeug.exceptions import Forbidden


@bp.route("/")
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def tags():
    return render_template("tag/tags.html", title="Tags")


@bp.route("/new", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def create():
    if len(current_user.tags) == current_user.tag_limit:
        flash(
            "You have reached the {0} tag limit for your account. "
            "Please delete an existing tag in order to create a new one.".format(current_user.tag_limit),
            "warning",
        )
        return redirect(url_for("tag.tags"))
    form = TagForm()
    if form.validate_on_submit():
        tag = Tag(user_id=current_user.id, name=form.name.data.strip())
        db.session.add(tag)
        db.session.commit()
        flash("Tag has been created.", "success")
        return redirect(url_for("tag.tags"))
    return render_template("tag/create_tag_form.html", title="Create tag", form=form)


@bp.route("/<uuid:id>", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def update(id):
    tag = Tag.query.get_or_404(str(id), description="Tag not found")
    if tag not in current_user.tags:
        raise Forbidden()
    form = TagForm()
    if form.validate_on_submit():
        tag.name = form.name.data.strip()
        tag.updated_at = pytz.utc.localize(datetime.utcnow())
        db.session.add(tag)
        db.session.commit()
        flash("Tag has been saved.", "success")
        return redirect(url_for("tag.tags"))
    elif request.method == "GET":
        form.name.data = tag.name
    return render_template("tag/update_tag_form.html", title="Edit tag", form=form, tag=tag)


@bp.route("/<uuid:id>/delete", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def delete(id):
    tag = Tag.query.get_or_404(str(id), description="Tag not found")
    if tag not in current_user.tags:
        raise Forbidden()
    if request.method == "GET":
        return render_template("tag/delete_tag.html", title="Delete tag", tag=tag)
    elif request.method == "POST":
        db.session.delete(tag)
        db.session.commit()
        flash("Tag has been deleted.", "success")
        return redirect(url_for("tag.tags"))


@bp.route("/<uuid:id>/entries", methods=["GET"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def entries(id):
    tag = Tag.query.get_or_404(str(id), description="Tag not found")

    now = pytz.utc.localize(datetime.utcnow())

    return render_template("tag/entries.html", title="{} time entries".format(tag.name), events=tag.events, now=now)
