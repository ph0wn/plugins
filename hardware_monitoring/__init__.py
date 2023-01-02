from flask import current_app as app, render_template, request, redirect, jsonify, url_for, Blueprint
from CTFd.utils.decorators import admins_only, authed_only
from CTFd.utils.user import is_admin, get_current_team, get_current_user
from CTFd.schemas.notifications import NotificationSchema
from CTFd.models import Challenges, db, Notifications
from CTFd.plugins import bypass_csrf_protection, register_user_page_menu_bar
from . import utils
from .models import Queue, Slot
from time import time
from collections import namedtuple


def load(app):
    app.db.create_all()
    admin_hardware_monitoring = Blueprint('admin_hardware_monitoring', __name__, template_folder='templates')
    authed_hardware_monitoring = Blueprint('authed_hardware_monitoring', __name__, template_folder='templates')

    @admin_hardware_monitoring.route('/admin/hardware_monitoring', methods=['GET'])
    @admins_only
    def view_panel():
        challenges = Challenges.query.all()
        queues = Queue.query.all()
        slots = Slot.query.all()
        return render_template('home.html', challenges=challenges, queues=queues, slots=slots)

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/create_queue', methods=['POST'])
    @admins_only
    @bypass_csrf_protection
    def create_queue():
        equipment_name = request.form.get('equipment_name')
        challenge_name = request.form.get('challenge_name')
        start = request.form.get('start')
        end = request.form.get('end')
        interval = int(request.form.get('interval'))
        existing_queue = Queue.query.filter_by(equipment_name=equipment_name).first()
        if existing_queue is None:
            utils.create_queue(equipment_name, challenge_name, start, end, interval)
        return redirect(url_for('admin_hardware_monitoring.view_panel'))

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/<int:queue_id>/delete_queue', methods=['POST'])
    @admins_only
    def delete_queue(queue_id):
        queue = Queue.query.filter_by(id=queue_id).first_or_404()
        equipment_name = queue.equipment_name
        slots = Slot.query.filter_by(equipment_name=equipment_name).all()
        for slot in slots:
            db.session.delete(slot)
        db.session.delete(queue)
        db.session.commit()
        db.session.close()
        return '1'

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/<int:slot_id>/free_slot', methods=['POST'])
    @authed_only
    def free_slot(slot_id):
        slot = Slot.query.filter_by(id=slot_id).first_or_404()
        if is_admin() or get_current_team().name == slot.team_name:
            if slot.filled:
                slot.filled = False
                slot.team_name = ""
                db.session.commit()
        db.session.close()
        return '1'

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/set_queue_state', methods=['POST'])
    @admins_only
    def set_queue_state():
        queue_id = request.form.get('queue_id')
        target_state = request.form.get('target_state')
        queue = Queue.query.filter_by(id=queue_id).first_or_404()
        queue.state = target_state
        if target_state == "being_prepared":
            slot = Slot.query.filter_by(equipment_name=queue.equipment_name, team_name=queue.team_name).first()
            if slot is not None:
                slot.over = True
            queue.team_name = ""
        elif target_state == "ready":
            # what is the name of the next team
            slots = Slot.query.filter_by(equipment_name=queue.equipment_name, over=False)
            for s in slots:
                if s.team_name is not None and s.team_name != '':
                    '''
                    In the end we remove notifications because there are too many
                    
                    content = f"Dear {s.team_name}, your hardware {queue.equipment_name} " \
                              f"for challenge {queue.challenge_name} is ready. Come and pick it up! --Ph0wn Admins"
                    req = {'type': 'alert',
                           'sound': False,
                           'title': f"Attention to {s.team_name} / Hardware Ready",
                           'user_id': get_current_user().id,
                           'content': content
                           }
                    schema = NotificationSchema()
                    result = schema.load(req)
                    db.session.add(result.data)
                    db.session.commit()
                    response = schema.dump(result.data)
                    app.events_manager.publish(data=response.data, type="notification")
                    '''
                    break

        db.session.commit()
        db.session.close()
        return '1'

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/set_in_use', methods=['POST'])
    @admins_only
    def set_in_use():
        slot_id = request.form.get('slot_id')
        slot = Slot.query.filter_by(id=slot_id).first_or_404()
        queue = Queue.query.filter_by(equipment_name=slot.equipment_name).first_or_404()
        queue.state = "in_use"
        slot.over = False
        queue.team_name = slot.team_name
        db.session.commit()
        db.session.close()
        return '1'

    @admin_hardware_monitoring.route('/admin/hardware_monitoring/delay_slots', methods=['POST'])
    @admins_only
    def delay_slots():
        equipment_name = request.form.get('equipment_name')
        delay = int(request.form.get('delay'))
        queue = Queue.query.filter_by(equipment_name=equipment_name).first_or_404()
        queue.end = utils.delay_time(queue.end, delay)
        slots = Slot.query.filter_by(equipment_name=equipment_name, over=False)
        for s in slots:
            s.start = utils.delay_time(s.start, delay)
            s.end = utils.delay_time(s.end, delay)
        db.session.commit()
        db.session.close()
        return redirect(url_for('admin_hardware_monitoring.view_panel'))

    app.register_blueprint(admin_hardware_monitoring)

    @authed_hardware_monitoring.route('/hardware_monitoring', methods=['GET'])
    @authed_only
    def view_hwm():
        queues = Queue.query.all()
        slots = Slot.query.filter_by(over=False)
        team_name = get_current_team().name
        return render_template('hwm.html', queues=queues, slots=slots, team_name=team_name)

    @authed_hardware_monitoring.route('/hardware_monitoring/<int:slot_id>/book_slot', methods=['POST'])
    @authed_only
    def book_slot(slot_id):
        team_name = get_current_team().name
        slot = Slot.query.filter_by(id=slot_id).first_or_404()
        slots_team_chall = Slot.query.filter_by(team_name=team_name, equipment_name=slot.equipment_name, over=False)
        if len(list(slots_team_chall)) == 0 and not slot.filled:
            slot.filled = True
            slot.team_name = team_name
            db.session.commit()
        db.session.close()
        return '1'

    app.register_blueprint(authed_hardware_monitoring)
    Menu = namedtuple("Menu", ["title", "route"])
    register_user_page_menu_bar("Hardware", "/hardware_monitoring")
