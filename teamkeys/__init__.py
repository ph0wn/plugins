from flask import current_app as app, render_template, request, redirect, abort, jsonify, url_for, session, Blueprint, Response, send_file
from functools import wraps
from CTFd.models import db, Teams
from CTFd import utils
from CTFd.utils.plugins import override_template
import json
# from .models import TeamKey
import logging
import os
from os.path import join, dirname, realpath, isdir, isfile

logger = logging.getLogger('teamkeys plugin')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

TEAM_KEYS_DIR = join(dirname(realpath(__file__)), 'team-keys')
assert isdir(TEAM_KEYS_DIR)


def get_team_keys(team_id):
    # It returns {'label1' : 'val1', 'label2' : 'val2', ... }, or None in case of errors

    logger.debug("get_team_keys for team_id={}".format(team_id))
    team_keys_fp = join(TEAM_KEYS_DIR, 'team-{}.json'.format(team_id))
    if not isfile(team_keys_fp):
        logger.error("Could not find team-{}.json".format(team_id))
        return None

    try:
        with open(team_keys_fp) as f:
            keys = json.load(f)
    except Exception as e:
        logger.error("Exception in get team keys team_id={}".format(team_id))
        keys = None

    logger.debug("Retrieved keys for {}".format(team_id))
    return keys


def load(app):
    app.db.create_all()

    logger.debug("loading team key plugin")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(dir_path, './templates/teamkeys.html')
    override_template('teamkeys.html', open(template_path).read())

    @app.route('/teamkeys', methods=['GET'])
    def view_teamkeys():
        if utils.user.authed():
            team_id = session['id']
            teamkeys = get_team_keys(team_id=team_id)
            return render_template('teamkeys.html', teamkeys=teamkeys, team_id=team_id)
        else:
            return redirect(url_for('auth.login'))
