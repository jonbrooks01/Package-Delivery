# time_utils.py
#
# Produces results for when an individual inputs a random time
#

from datetime import timedelta

AVERAGE_MPH = 18.0


def parse_clock(text):
    cleaned = text.strip().upper()

    if cleaned == "EOD":
        return None
    is_pm = cleaned.endswith("PM")
    has_meridiem = is_pm or cleaned.endswith("AM")
    if has_meridiem:
        cleaned = cleaned[:-2].strip()

    hour_text, minute_text = cleaned.split(":")
    hour = int(hour_text)
    minute = int(minute_text)

    if has_meridiem:
        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0

    return timedelta(hours=hour, minutes=minute)


def format_clock(value):
    if value is None:
        return "EOD"

    total_minutes = int(value.total_seconds() // 60)
    hour, minute = divmod(total_minutes, 60)

    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12

    return "%d:%02d %s" % (hour_12, minute, suffix)


def travel_time(miles, mph=AVERAGE_MPH):
    return timedelta(hours=miles / mph)

