# -*- coding: utf-8 -*-

from uuid import uuid4

from flask import (Blueprint, render_template, current_app, request,
                   flash, url_for, redirect, session, abort)
from flask.ext.mail import Message
from flask.ext.babel import gettext as _
from flask.ext.login import (login_required, login_user, current_user,
                            logout_user, confirm_login, login_fresh)

from webapp.models import User
from webapp.extensions import db, mail, login_manager, facebook
from webapp.forms import (SignupForm, LoginForm, RecoverPasswordForm,
                         ChangePasswordForm, ReauthForm)


frontend = Blueprint('frontend', __name__)



@frontend.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(login=request.args.get('login', None),
                     next=request.args.get('next', None))

    if form.validate_on_submit():
        user, authenticated = User.authenticate(form.login.data,
                                    form.password.data)

        if user and authenticated:
            remember = request.form.get('remember') == 'y'
            if login_user(user, remember=remember):
                flash("Logged in!", 'success')
            return redirect(form.next.data or url_for('search.index'))
        else:
            flash(_('Sorry, invalid login'), 'error')

    return render_template('login.html', form=form)


@frontend.route('/reauth', methods=['GET', 'POST'])
@login_required
def reauth():
    form = ReauthForm(next=request.args.get('next'))

    if request.method == 'POST':
        user, authenticated = User.authenticate(current_user.name,
                                    form.password.data)
        if user and authenticated:
            confirm_login()
            current_app.logger.debug('reauth: %s' % session['_fresh'])
            flash(_('Reauthenticated.'), 'success')
            return redirect('/change_password')

        flash(_('Password is wrong.'), 'error')
    return render_template('reauth.html', form=form)


@frontend.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You are now logged out'), 'success')
    return redirect(url_for('search.index'))


@frontend.route('/signup', methods=['GET', 'POST'])
def signup():
    login_form= LoginForm(next=request.args.get('next'))
    form = SignupForm(next=request.args.get('next'))

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        if login_user(user):
            return redirect(form.next.data or url_for('search.index'))

    return render_template('signup.html', form=form, login_form=login_form)


@frontend.route('/change_password', methods=['GET', 'POST'])
def change_password():
    user = None
    if current_user.is_authenticated():
        if not login_fresh():
            return login_manager.needs_refresh()
        user = current_user
    elif 'activation_key' in request.values and 'email' in request.values:
        activation_key = request.values['activation_key']
        email = request.values['email']
        user = User.query.filter_by(activation_key=activation_key) \
                         .filter_by(email=email).first()

    if user is None:
        abort(403)

    form = ChangePasswordForm(activation_key=user.activation_key)

    if form.validate_on_submit():
        user.password = form.password.data
        user.activation_key = None
        db.session.add(user)
        db.session.commit()

        flash(_("Your password has been changed, please log in again"),
              "success")
        return redirect(url_for("login.login"))

    return render_template("change_password.html", form=form)


@frontend.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = RecoverPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            flash(_('Please see your email for instructions on '
                  'how to access your account'), 'success')

            user.activation_key = str(uuid4())
            db.session.add(user)
            db.session.commit()

            body = render_template('emails/reset_password.html', user=user)
            message = Message(subject=_('Recover your password'), body=body,
                              recipients=[user.email])
            mail.send(message)

            return redirect(url_for('search.index'))
        else:
            flash(_('Sorry, no user found for that email address'), 'error')

    return render_template('reset_password.html', form=form)

# Facebook
@frontend.route('/login_fb')
def login_fb():
    return facebook.authorize(callback=url_for('frontend.facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@frontend.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    session['fb_name'] = None
    if resp is None:
        session['fb_name'] = "Facebook login error"
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    session['fb_name'] = me.data['name']
    return redirect(url_for('search.index'))
    #return 'Logged in as id=%s name=%s redirect=%s' % \
        #(me.data['id'], me.data['name'], url_for("search.index"))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@frontend.route('/about')
def about():
    return '<h1>About Page</h1>'


@frontend.route('/blog')
def blog():
    return '<h1>Blog Page</h1>'


@frontend.route('/help')
def help():
    return '<h1>Help Page</h1>'


@frontend.route('/terms')
def terms():
    return '<h1>Terms Page</h1>'
