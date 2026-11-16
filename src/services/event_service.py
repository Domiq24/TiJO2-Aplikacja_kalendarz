import calendar
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from services.db import events_collection


def add_months(dt, months):
  month = dt.month - 1 + months
  year = dt.year + month // 12
  month = month % 12 + 1
  day = min(dt.day, calendar.monthrange(year, month)[1])
  return dt.replace(year=year, month=month, day=day)


def add_years(dt, years):
  year = dt.year + years
  day = min(dt.day, calendar.monthrange(year, dt.month)[1])
  return dt.replace(year=year, day=day)


def get_expanded_events(user_id, range_start, range_end):
  raw_events = list(events_collection.find({"user_id": user_id}))
  expanded = []

  for ev in raw_events:
    start = ev["start_time"]
    end = ev["end_time"]
    recurrence = ev.get("recurrence", "none")

    if recurrence == "none":
      if start < range_end and end > range_start:
        expanded.append({
            "_id": ev["_id"],
            "title": ev["title"],
            "description": ev.get("description", ""),
            "start_time": start,
            "end_time": end,
            "recurrence": recurrence,
        })
    elif recurrence == "weekly":
      current_start = start
      current_end = end
      if current_start > range_end:
        continue
      while current_start < range_end:
        if current_end > range_start and current_start < range_end:
          expanded.append({
              "_id": ev["_id"],
              "title": ev["title"],
              "description": ev.get("description", ""),
              "start_time": current_start,
              "end_time": current_end,
              "recurrence": recurrence,
          })
        current_start += timedelta(days=7)
        current_end += timedelta(days=7)
    elif recurrence == "monthly":
      current_start = start
      current_end = end
      if current_start > range_end:
        continue
      while current_start < range_end:
        if current_end > range_start and current_start < range_end:
          expanded.append({
              "_id": ev["_id"],
              "title": ev["title"],
              "description": ev.get("description", ""),
              "start_time": current_start,
              "end_time": current_end,
              "recurrence": recurrence,
          })
        duration = current_end - current_start
        current_start = add_months(current_start, 1)
        current_end = current_start + duration
    elif recurrence == "yearly":
      current_start = start
      current_end = end
      if current_start > range_end:
        continue
      while current_start < range_end:
        if current_end > range_start and current_end < range_end:
          expanded.append({
              "_id": ev["_id"],
              "title": ev["title"],
              "description": ev.get("description", ""),
              "start_time": current_start,
              "end_time": current_end,
              "recurrence": recurrence,
          })
        duration = current_end - current_start
        current_start = add_years(current_start, 1)
        current_end = current_start + duration

  return expanded


def calculate_event_columns(events):
  """Algorytm przypisujący kolumny nakładającym się wydarzeniom bez limitu"""
  if not events:
    return []

  # Sortowanie po czasie startu, a następnie malejąco po czasie trwania
  sorted_events = sorted(
      events,
      key=lambda x: (
          x["start_time"],
          -(x["end_time"] - x["start_time"]).total_seconds(),
      ),
  )

  # Podział na niezależne klastry nachodzących na siebie wydarzeń
  clusters = []
  current_cluster = []
  cluster_end = None

  for ev in sorted_events:
    s = ev["start_time"]
    e = ev["end_time"]
    if not current_cluster:
      current_cluster.append(ev)
      cluster_end = e
    else:
      if s < cluster_end:
        current_cluster.append(ev)
        if e > cluster_end:
          cluster_end = e
      else:
        clusters.append(current_cluster)
        current_cluster = [ev]
        cluster_end = e
  if current_cluster:
    clusters.append(current_cluster)

  processed_events = []

  # Przypisanie indeksów kolumn wewnątrz każdego klastra
  for cluster in clusters:
    col_ends = []
    cluster_assignments = []

    for ev in cluster:
      s = ev["start_time"]
      e = ev["end_time"]

      placed = False
      for i, ce in enumerate(col_ends):
        if ce <= s:
          col_ends[i] = e
          cluster_assignments.append((ev, i))
          placed = True
          break
      if not placed:
        col_ends.append(e)
        cluster_assignments.append((ev, len(col_ends) - 1))

    total_cols = len(col_ends)
    for ev, col_idx in cluster_assignments:
      ev_copy = ev.copy()
      ev_copy["col_index"] = col_idx
      ev_copy["total_cols"] = total_cols
      processed_events.append(ev_copy)

  return processed_events


def get_events_for_month(user_id, year, month):
  start_date = datetime(year, month, 1)
  if month == 12:
    end_date = datetime(year + 1, 1, 1)
  else:
    end_date = datetime(year, month + 1, 1)
  return get_expanded_events(user_id, start_date, end_date)


def get_events_for_day(user_id, day_date):
  next_day = day_date + timedelta(days=1)
  events = get_expanded_events(user_id, day_date, next_day)
  events = calculate_event_columns(events)
  events.sort(key=lambda x: x["start_time"].time())
  return events


def add_event(
    user_id,
    title,
    description,
    date_str,
    start_time_str,
    end_time_str,
    recurrence="none",
):
  start_datetime = datetime.strptime(
      f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M"
  )
  end_datetime = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")

  if end_datetime <= start_datetime:
    raise ValueError(
        "Czas zakończenia musi być późniejszy niż czas rozpoczęcia."
    )

  events_collection.insert_one({
      "user_id": user_id,
      "title": title,
      "description": description,
      "start_time": start_datetime,
      "end_time": end_datetime,
      "recurrence": recurrence,
  })


def update_event(
    user_id,
    event_id,
    title,
    description,
    date_str,
    start_time_str,
    end_time_str,
    recurrence="none",
):
  start_datetime = datetime.strptime(
      f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M"
  )
  end_datetime = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")

  if end_datetime <= start_datetime:
    raise ValueError(
        "Czas zakończenia musi być późniejszy niż czas rozpoczęcia."
    )

  events_collection.update_one(
      {"_id": ObjectId(event_id), "user_id": user_id},
      {
          "$set": {
              "title": title,
              "description": description,
              "start_time": start_datetime,
              "end_time": end_datetime,
              "recurrence": recurrence,
          }
      },
  )


def delete_event(user_id, event_id):
  events_collection.delete_one({"_id": ObjectId(event_id), "user_id": user_id})