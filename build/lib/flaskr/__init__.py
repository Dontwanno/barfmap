import os
from datetime import datetime
from flask import Flask
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required, JWTManager


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    jwt = JWTManager(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    @app.route("/time")
    def time():
        return jsonify(datetime.now())

    @app.route('/token', methods=["POST"])
    def create_token():
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        if email != "test" or password != "test":
            return {"msg": "Wrong email or password"}, 401

        access_token = create_access_token(identity=email)
        response = {"access_token": access_token}
        return response

    @app.route('/profile')
    @jwt_required()
    def my_profile():
        response_body = {
            "name": "Nagato",
            "about": "Hello! I'm a full stack developer that loves python and javascript"
        }
        return response_body

    @app.route("/logout", methods=["POST"])
    def logout():
        response = jsonify({"msg": "logout successful"})
        unset_jwt_cookies(response)
        return response

    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                data = response.get_json()
                if type(data) is dict:
                    data["access_token"] = access_token
                    response.data = json.dumps(data)
            return response
        except (RuntimeError, KeyError):
            # Case where there is not a valid JWT. Just return the original respone
            return response



    # register the database commands
    from flaskr import db

    db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth

    app.register_blueprint(auth.bp)

    from flaskr import feed
    app.register_blueprint(feed.bp)
    app.add_url_rule('/', endpoint='index')

    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    return app
