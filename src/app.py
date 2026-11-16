from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from services.auth_service import authenticate_user, register_user
from services.calendar_service import get_month_data
from services.event_service import (
    add_event as service_add_event,
    delete_event as service_delete_event,
    get_events_for_day,
    get_events_for_month,
    update_event as service_update_event,
)
from services.ics_service import generate_ics_for_events

app = Flask(__name__)
app.secret_key = "twoj_tajny_klucz_sesji"


def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if "user_id" not in session:
      flash("Najpierw zaloguj się do systemu.", "warning")
      return redirect(url_for("login"))
    return f(*args, **kwargs)

  return decorated_function


@app.route("/")
def index():
  if "user_id" not in session:
    return redirect(url_for("login"))
  now = datetime.now()
  return redirect(url_for("month_view", year=now.year, month=now.month))


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    user_id = authenticate_user(username, password)
    if user_id:
      session["user_id"] = user_id
      session["username"] = username
      flash("Zalogowano pomyślnie!", "success")
      return redirect(url_for("index"))
    else:
      flash("Błędna nazwa użytkownika lub hasło.", "danger")
  return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")  # Pobranie drugego hasła

    try:
      register_user(username, password, confirm_password)  # Przekazanie do serwisu
      flash("Konto utworzone! Możesz się zalogować.", "success")
      return redirect(url_for("login"))
    except ValueError as e:
      flash(str(e), "danger")
  return render_template("register.html")


@app.route("/logout")
def logout():
  session.clear()
  flash("Wylogowano pomyślnie.", "info")
  return redirect(url_for("login"))


@app.route("/calendar/<int:year>/<int:month>")
@login_required
def month_view(year, month):
  data = get_month_data(session["user_id"], year, month)
  return render_template("month.html", **data)


@app.route("/day/<date_str>")
@login_required
def day_view(date_str):
  day_date = datetime.strptime(date_str, "%Y-%m-%d")
  events = get_events_for_day(session["user_id"], day_date)
  return render_template(
      "day.html", date_str=date_str, day_date=day_date, events=events
  )


@app.route("/add_event", methods=["POST"])
@login_required
def add_event():
  title = request.form.get("title")
  description = request.form.get("description")
  date_str = request.form.get("date")
  start_time_str = request.form.get("start_time")
  end_time_str = request.form.get("end_time")
  recurrence = request.form.get("recurrence", "none")

  try:
    service_add_event(
        session["user_id"],
        title,
        description,
        date_str,
        start_time_str,
        end_time_str,
        recurrence,
    )
    flash("Wydarzenie dodane pomyślnie!", "success")
  except ValueError as e:
    flash(str(e), "danger")

  return redirect(url_for("day_view", date_str=date_str))


@app.route("/edit_event/<event_id>", methods=["POST"])
@login_required
def edit_event(event_id):
  title = request.form.get("title")
  description = request.form.get("description")
  date_str = request.form.get("date")
  start_time_str = request.form.get("start_time")
  end_time_str = request.form.get("end_time")
  recurrence = request.form.get("recurrence", "none")

  try:
    service_update_event(
        session["user_id"],
        event_id,
        title,
        description,
        date_str,
        start_time_str,
        end_time_str,
        recurrence,
    )
    flash("Wydarzenie zaktualizowane.", "success")
  except ValueError as e:
    flash(str(e), "danger")

  return redirect(url_for("day_view", date_str=date_str))


@app.route("/delete_event/<event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
  date_str = request.form.get("date")
  service_delete_event(session["user_id"], event_id)
  flash("Wydarzenie usunięte.", "info")
  return redirect(url_for("day_view", date_str=date_str))


@app.route("/export/month/<int:year>/<int:month>")
@login_required
def export_month_ics(year, month):
  events = get_events_for_month(session["user_id"], year, month)
  ics_content = generate_ics_for_events(events, f"Kalendarz_{month}_{year}")
  return Response(
      ics_content,
      mimetype="text/calendar",
      headers={
          "Content-Disposition": f"attachment; filename=kalendarz_{year}_{month:02d}.ics"
      },
  )


if __name__ == "__main__":
  app.run(debug=True)