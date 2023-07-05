
import calendar
import json
import requests
import pprint

from datetime import datetime, date, timezone


def get_current_month():
    today = date.today()
    return today.strftime("%Y-%m")


def get_total_worked_hours(api_key, workspace_id, user_id):
    headers = {
        "content-type": "application/json",
        "X-Api-Key": api_key,
    }

    url = f"https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user_id}/time-entries"

    # Get the current month
    current_month = get_current_month()

    # Calculate the first and last day of the month
    first_day = current_month + "-01"
    last_day = datetime.now().strftime("%Y-%m-%d")

    # Query parameters to filter time entries for the current month
    params = {
        "start": f"{first_day}T00:00:00Z",
        "end": f"{last_day}T23:59:59Z",
    }

    response = requests.get(url, headers=headers, params=params)
    time_entries = response.json()

    total_hours = 0

    for entry in time_entries:
        start_time = datetime.fromisoformat(entry["timeInterval"]["start"].rstrip("Z")).replace(tzinfo=timezone.utc)

        if entry["timeInterval"]["end"] is not None:
            end_time = datetime.fromisoformat(entry["timeInterval"]["end"].rstrip("Z")).replace(tzinfo=timezone.utc)
        else:
            end_time = datetime.now(timezone.utc)

        # Calculate the duration of the time entry
        duration = end_time - start_time
        total_hours += duration.total_seconds() / 3600

    return total_hours


def calculate_hours_per_month(api_key, workspace_id, user_id):
    # Get the total worked hours for the current month
    total_hours = get_total_worked_hours(api_key, workspace_id, user_id)

    # Get the number of days passed in the current month
    today = date.today()
    days_passed = today.day

    # Days in a month
    now = datetime.now()
    _, days_in_month = calendar.monthrange(now.year, now.month)

    # Calculate the hours per month rate
    hours_per_month = total_hours / days_passed * days_in_month

    return hours_per_month, total_hours

def get_user_id(api_key):
    headers = {
        "content-type": "application/json",
        "X-Api-Key": api_key,
    }

    url = "https://api.clockify.me/api/v1/user"

    response = requests.get(url, headers=headers)
    user_data = response.json()

    return user_data["id"]


def get_workspace_id(api_key):
    headers = {
        "content-type": "application/json",
        "X-Api-Key": api_key,
    }

    url = "https://api.clockify.me/api/v1/workspaces"

    response = requests.get(url, headers=headers)
    workspaces_data = response.json()

    # Assuming the user has only one workspace, return its ID
    return workspaces_data[0]["id"]

# Read IDs from JSON file
with open("config.json") as file:
    data = json.load(file)
    API_KEY = data["api_key"]
    HOURS_THIS_MONTH = data["hours_this_month"]

# Get user ID and workspace ID based on the API key
USER_ID = get_user_id(API_KEY)
WORKSPACE_ID = get_workspace_id(API_KEY)

# Total worked hours
hours = get_total_worked_hours(API_KEY, WORKSPACE_ID, USER_ID)

# Get the number of days passed in the current month
today = date.today()
days_passed = today.day

# Days in a month
now = datetime.now()
_, days_in_month = calendar.monthrange(now.year, now.month)

# Calculate the pessimistic hours per month rate
rate = hours / days_passed * days_in_month

# Calculate the pessimistic hours per month rate
hours_per_month_pessimistic = hours / min(days_passed + 2, days_in_month) * days_in_month

# Calculate where we should be in the month-plus-two
hours_planned = HOURS_THIS_MONTH / days_in_month * min(days_passed + 2, days_in_month)

hours_ahead = hours - hours_planned

days_ahead = hours_ahead / (HOURS_THIS_MONTH / days_in_month)

# this should be a compact flag but right now it isn't
if True:
    print(f"<center>{hours:.1f} / {HOURS_THIS_MONTH:.1f} - {days_ahead:+.2f}</center>")
else:
    print(f"Current hours so far this month: {hours:2f} hours")
    print(f"Current hours per month rate: {rate:.2f} hours")
    print(f"Current hours per month rate pessimistic: {hours_per_month_pessimistic:.2f} hours")
    print(f"Current pessimistic speed in percent: {hours_per_month_pessimistic / HOURS_THIS_MONTH * 100:2f}%")
