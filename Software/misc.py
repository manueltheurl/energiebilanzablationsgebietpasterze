import datetime as dt
import numpy as np


"""
Misc module, could of course be another class with static and classmethods as well. But as there are no module
variables, it does not really make any difference. Various functions for various things are inside of here.
"""


def set_widget_state(widgets: list, state):
    if state == 1 or state == "normal":  # actually check if its 1 or 0, cause else "disabled" string is True also
        for widget in widgets:
            widget["state"] = "normal"

    elif state == 0 or state == "disabled":
        for widget in widgets:
            widget["state"] = "disabled"

    elif state == "active":
        for widget in widgets:
            widget["state"] = "active"


def get_difference_of_months(earlier_month, later_month):
    return (later_month - earlier_month) % 12


def make_seconds_beautiful_string(seconds):
    days = seconds // 86400
    remaining_seconds = seconds % 86400

    hours = remaining_seconds // 3600
    remaining_seconds = remaining_seconds % 3600

    minutes = remaining_seconds // 60
    remaining_seconds = remaining_seconds % 60

    beautiful_string = []

    if days > 0:
        beautiful_string.append(str(int(days)) + " Days")
    if hours > 0:
        beautiful_string.append(str(int(hours)) + " Hour")
    if minutes > 0:
        beautiful_string.append(str(int(minutes)) + " Min")
    if remaining_seconds > 0:
        beautiful_string.append(str(int(remaining_seconds)) + " Sec")

    return " ".join(beautiful_string)


def string_date_to_datetime(string_date):
    try:
        return dt.datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S")  # double quotes around date
    except ValueError:
        return dt.datetime.strptime(string_date, "\"%Y-%m-%d %H:%M:%S\"")  # double quotes around date


values_to_check_for_change = {
    "years_passed": None
}


def value_changed(value, value_name):
    if values_to_check_for_change[value_name] != value:
        values_to_check_for_change[value_name] = value
        return True
    return False


def remove_none_in_lists(lists):
    none_indexes = []
    for i, values in enumerate(zip(*lists)):
        if None in values:
            none_indexes.append(i)

    return_lists = []

    for list_ in lists:
        return_lists.append(np.delete(list_, none_indexes))

    return return_lists


def save_add(first, second):
    if None not in [first, second]:
        return first + second
    return None
