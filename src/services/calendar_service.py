import calendar
from services.event_service import get_events_for_month

# Słownik z polskimi nazwami miesięcy
POLISH_MONTHS = {
    1: "Styczeń",
    2: "Luty",
    3: "Marzec",
    4: "Kwiecień",
    5: "Maj",
    6: "Czerwiec",
    7: "Lipiec",
    8: "Sierpień",
    9: "Wrzesień",
    10: "Październik",
    11: "Listopad",
    12: "Grudzień",
}


def get_month_data(user_id, year, month):
  prev_month = month - 1 if month > 1 else 12
  prev_year = year if month > 1 else year - 1
  next_month = month + 1 if month < 12 else 1
  next_year = year if month < 12 else year + 1

  cal = calendar.monthcalendar(year, month)
  events = get_events_for_month(user_id, year, month)

  event_counts = {}
  for event in events:
    day_str = event["start_time"].strftime("%Y-%m-%d")
    event_counts[day_str] = event_counts.get(day_str, 0) + 1

  # Pobieranie polskiej nazwy miesiąca ze słownika
  month_name = POLISH_MONTHS.get(month, "")

  return {
      "year": year,
      "month": month,
      "month_name": month_name,
      "calendar_matrix": cal,
      "event_counts": event_counts,
      "prev_year": prev_year,
      "prev_month": prev_month,
      "next_year": next_year,
      "next_month": next_month,
  }