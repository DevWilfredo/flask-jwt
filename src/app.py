"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User
from sqlalchemy import select
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# from models import Person

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../dist/')
app = Flask(__name__)
# Change this "super secret" to something else!
app.config["JWT_SECRET_KEY"] = "super-secret"

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
app.url_map.strict_slashes = False

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)
CORS(app)
# Add all endpoints form the API with a "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoint


@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    results = list(map(lambda x: x.serialize(), users))
    return jsonify(results), 200


@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        return jsonify({'message': '1 or more credentials are missing'}), 500
    hashed_password = bcrypt.generate_password_hash(
        password).decode('utf-8')
    newUser = User(email=email, password=hashed_password, is_active=True)
    db.session.add(newUser)
    db.session.commit()
    return jsonify({'message': 'User created succesfully'})


@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        return jsonify({'message': '1 or more credentials are missing'}), 500
    user = db.session.execute(select(User).where(
        User.email == email)).scalar_one_or_none()
    if user is None:
        return jsonify({'message': 'user not found'}), 500
    valid_password = bcrypt.check_password_hash(user.password, password)
    if not valid_password:
        return jsonify({'message': 'user not found'}), 500
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'message': 'Login succesfully', 'data': {'token': access_token, "user_id": user.id}})


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({"id": user.id, "email": user.email}), 200


# any other endpoint will try to serve it like a static file


@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
