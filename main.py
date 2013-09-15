# vim:fileencoding=utf-8:

from flask import Flask, request, render_template, redirect, url_for, make_response

app = Flask('app')
app.debug = True

from google.appengine.api import users
from google.appengine.ext import db

import functools
import datetime

################################################################################

class RegisteredUser(db.Model):
  user = db.UserProperty(auto_current_user=True)
  lastused = db.DateTimeProperty(auto_now=True)

class DataEntry(db.Model):
  user = db.UserProperty(auto_current_user=True)
  date = db.DateProperty()
  updated = db.DateTimeProperty(auto_now=True)
  memo = db.TextProperty()

report_start = datetime.date(2013, 9, 1)
report_days = 60

################################################################################

def login_required(func):
  @functools.wraps(func)
  def decorated(*args, **kw):
    user = users.get_current_user()
    if user:
      u = RegisteredUser.all().filter('user =', user).get()
      (u or RegisteredUser()).put()
      return func(*args, **kw)
    return redirect(users.create_login_url())
  return decorated

def render(template, **kw):
  kw['user'] = users.get_current_user()
  kw['logout'] = users.create_logout_url('/')
  resp = make_response(render_template(template, **kw))
  resp.headers['Cache-Control'] = 'no-cache'
  resp.headers['Pragma'] = 'no-cache'
  resp.headers['Expires'] = '0'
  return resp

@app.route('/')
@login_required
def top():
  reports = {}
  for e in DataEntry.all().filter('user =', users.get_current_user()):
    reports[e.date] = e
  days = []
  for day in (report_start + datetime.timedelta(i) for i in range(report_days)):
    days.append(day)
  return render('top.html', days=days, reports=reports)

@app.route('/e/<int:year>-<int:month>-<int:day>/')
@login_required
def show_entry(year, month, day):
  date = datetime.date(year, month, day)
  entry = DataEntry.all()
  entry = entry.filter('user =', users.get_current_user())
  entry = entry.filter('date =', date)
  entry = entry.get()

  if not entry:
    return redirect(url_for('edit_entry', year=year, month=month, day=day))
  return render('show_entry.html', date=date, entry=entry)

@app.route('/e/<int:year>-<int:month>-<int:day>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(year, month, day):
  date = datetime.date(year, month, day)
  entry = DataEntry.all()
  entry = entry.filter('user =', users.get_current_user())
  entry = entry.filter('date =', date)
  entry = entry.get()

  if request.method == 'POST':
    if not entry:
      entry = DataEntry(date=date)
    entry.memo = request.form['memo']
    entry.put()
    resp = make_response()
    resp.headers['Refresh'] = '0; URL=' + url_for('show_entry', year=year, month=month, day=day)
    return resp

  return render('edit_entry.html', date=date, entry=entry)
