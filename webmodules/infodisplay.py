import flask

# Routes for info display

blueprint = flask.Blueprint('infodisplay', __name__, template_folder='templates')
last_state = ""

@blueprint.route('/')
def info():
    return flask.render_template('screendisplayer.html')


@blueprint.route("/changed")
def content():
    global last_state
    with open("states/info", "r") as f:
        state = f.read()
        if state == last_state:
            return "Not changed, but do not cache", 204
        else:
            last_state = state
            return state, 200


@blueprint.route("/content")
def ifr():
    # Render
    return flask.render_template(last_state + '.html')