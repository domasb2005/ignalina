import flask

app = flask.Flask(__name__)

# Routes for info display
from webmodules.infodisplay import blueprint as info_display_blueprint

app.register_blueprint(info_display_blueprint, url_prefix='/info')

# Routes for gameflow display
from webmodules.gamedisplay import blueprint as game_display_blueprint

app.register_blueprint(game_display_blueprint, url_prefix='/gameflow')

# Routes for admin
from webmodules.admin import blueprint as admin_blueprint

app.register_blueprint(admin_blueprint, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True)
    app.run()
