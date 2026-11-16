from datetime import datetime


def generate_ics_for_events(events, calendar_name="Mój Kalendarz"):
  ics_lines = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//Flask Calendar App//PL",
      f"X-WR-CALNAME:{calendar_name}",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
  ]

  for ev in events:
    dtstart = ev["start_time"].strftime("%Y%m%dT%H%M%S")
    dtend = ev["end_time"].strftime("%Y%m%dT%H%M%S")
    summary = ev["title"]
    description = ev.get("description", "").replace("\n", "\\n")
    uid = str(ev["_id"]) + "_" + dtstart

    ics_lines.extend([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
    ])

  ics_lines.append("END:VCALENDAR")
  return "\r\n".join(ics_lines)