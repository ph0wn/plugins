from CTFd.utils.decorators import admins_only
from CTFd.utils.user import is_admin, get_current_team, get_current_user
from CTFd.cache import cache
from CTFd.models import db
from .models import Queue, Slot
from datetime import datetime


def datetimelocal_to_datetime(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M')

def clean_print_dt(dt):
    return dt.strftime("%H:%M %d-%m-%Y")

def time_in_range(start, end):
    """Return true if we are in the range [start, end]"""
    now = datetime.now()
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def delay_time(string_dt, minutes):
    dt = datetime.strptime(string_dt, "%H:%M %d-%m-%Y")
    new_dt = datetime.fromtimestamp(dt.timestamp() + minutes*60)
    return clean_print_dt(new_dt)

def create_queue(equipment_name,challenge_name,start,end,interval):
    start_dt = datetimelocal_to_datetime(start)
    end_dt = datetimelocal_to_datetime(end)
    start_clean = clean_print_dt(start_dt)
    end_clean = clean_print_dt(end_dt)
    queue = Queue(equipment_name,challenge_name,"",start_clean, end_clean, interval)
    db.session.add(queue)
    total_length_minutes = int((end_dt.timestamp() - start_dt.timestamp())//60)
    number_slots = int(total_length_minutes//(interval + 5))
    for i in range(number_slots):
        start_slot = datetime.fromtimestamp(start_dt.timestamp() + i * ((interval + 5) * 60))
        end_slot = datetime.fromtimestamp(start_dt.timestamp() + (i+1) * ((interval + 5) * 60) - 5*60)
        start_slot_clean = clean_print_dt(start_slot)
        end_slot_clean = clean_print_dt(end_slot)
        end_ts = start_dt.timestamp() + (i+1) * ((interval + 5) * 60) - 5*60
        filled = False
        team_name = ""
        slot = Slot(equipment_name,challenge_name,start_slot_clean,end_slot_clean,end_ts,filled,team_name)
        db.session.add(slot)
    db.session.commit()
    db.session.close()
    return True

