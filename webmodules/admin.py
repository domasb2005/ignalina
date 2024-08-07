import os

import flask
import flask_httpauth

# Routes for info display

blueprint = flask.Blueprint('admin', __name__, template_folder='templates')
auth = flask_httpauth.HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if username == 'atomine' and password == 'elektrine':
        return True
    return False


@blueprint.route('/')
@auth.login_required
def admin():
    return flask.render_template('admindash.html')


@blueprint.route('/restarthost', methods=['POST'])
@auth.login_required
def restart_host():
    os.system('echo 1234567 | sudo -S reboot')
    return flask.redirect('/admin/')


@blueprint.route('/restartgame', methods=['POST'])
@auth.login_required
def restart_game():
    os.system('loginctl terminate-user nojus')
    return flask.redirect('/admin/')
