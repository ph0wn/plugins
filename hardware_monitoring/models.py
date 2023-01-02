from CTFd.models import db


class Queue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(80))
    challenge_name = db.Column(db.String(80))
    state = db.Column(db.String(80))
    start = db.Column(db.String(80))
    end = db.Column(db.String(80))
    interval = db.Column(db.Integer)
    team_name = db.Column(db.String(80))

    def __init__(self, equipment_name, challenge_name,
                state, start, end, interval):
        self.equipment_name = equipment_name
        self.challenge_name = challenge_name
        self.state = state
        self.start = start
        self.end = end
        self.interval = interval
        self.team_name = ""


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(80))
    challenge_name = db.Column(db.String(80))
    start = db.Column(db.String(80))
    end = db.Column(db.String(80))
    end_ts = db.Column(db.Integer)
    filled = db.Column(db.Boolean)
    team_name = db.Column(db.String(80))
    over = db.Column(db.Boolean)

    def __init__(self, equipment_name, challenge_name, start, end, end_ts, filled, team_name):
        self.equipment_name = equipment_name
        self.challenge_name = challenge_name
        self.start = start
        self.end = end
        self.end_ts = end_ts
        self.filled = filled
        self.team_name = team_name
        self.over = False

