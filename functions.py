import datetime as dt


def set_widget_state(widgets: list, state):
    if state == 1 or state == "normal":  # actually check if its 1 or 0, cause else "disabled" string is True also
        for widget in widgets:
            widget["state"] = "normal"

    elif state == 0 or state == "disabled":
        for widget in widgets:
            widget["state"] = "disabled"


def string_date_to_datetime(string_date):
    try:
        return dt.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S")  # double quotes around date
    except ValueError:
        return dt.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S")  # double quotes around date