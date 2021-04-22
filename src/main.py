"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets, People, Favorites
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.environ.get('WT_SECRET_KEY')  # Change this!
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_users():

    # response_body = {
    #     "msg": "Hello, this is your GET /user response "
    # }
    user = User.query.all()
    request = list(map(lambda user:user.serialize(),user))

    return jsonify(request), 200

# Planets list
@app.route('/planets', methods=['GET'])
def get_planets():
    planet = Planets.query.all()
    request = list(map(lambda planet:planet.serialize(),planet))

    return jsonify(request), 200

@app.route('/planets/<int:position>', methods=['GET'])
def get_one_planet(position):
    planet = Planets.query.filter_by(id=position)
    request = list(map(lambda planet:planet.serialize(),planet))
    return jsonify(request), 200

# People list
@app.route('/people', methods=['GET'])
def get_people():
    person = People.query.all()
    request = list(map(lambda person:person.serialize(),person))

    return jsonify(request), 200

@app.route('/people/<int:position>', methods=['GET'])
def get_one_person(position):
    person = People.query.filter_by(id=position)
    request = list(map(lambda person:person.serialize(),person))
    return jsonify(request), 200

# Favorites list
@app.route('/favorites', methods=['GET'])
def get_favorites():
    favorites = Favorites.query.all()
    request = list(map(lambda favorite:favorite.serialize(),favorites))
    return jsonify(request), 200

# Add a favorite
@app.route('/favorites', methods=['POST'])
def add_new_favorite():
    # Collect data
    planet_idPostIncoming = request.json.get("planet_id", None)
    people_idPostIncoming = request.json.get("people_id", None)
    user_idPostIncoming = request.json.get("user_id", None)

    # Validate data

    # Validate if user exist
    if user_idPostIncoming is None:
        raise APIException('User not found', status_code=404)

    # Validate if planet and people id are both defined. Just can be define one.
    if (planet_idPostIncoming is not None) and (people_idPostIncoming is not None):
        raise APIException('Data given is invalid', status_code=404)

    # Validate if planet and people id are both None.
    if (planet_idPostIncoming is None) and (people_idPostIncoming is None):
        raise APIException('Data given is invalid', status_code=404)

    if planet_idPostIncoming != people_idPostIncoming:
        # Validate if people id exists.
        if planet_idPostIncoming is None:
            if people_idPostIncoming is None:
                raise APIException('Character not found', status_code=404)
        # Validate if planet id exists.
        if people_idPostIncoming is None:
            if planet_idPostIncoming is None:
                raise APIException('Planet not found', status_code=404)
    else:
        raise APIException('Data given is invalid', status_code=404)
    
    # Verify if favorite already exist
    favorite_exist = Favorites.query.filter_by(user_id=user_idPostIncoming, planet_id=planet_idPostIncoming, people_id=people_idPostIncoming).first()
    if favorite_exist is not None:
        raise APIException('Favorite already exist.', status_code=404)

    # Create instance to the model
    newFavorite = Favorites(planet_id = planet_idPostIncoming, people_id = people_idPostIncoming, user_id = user_idPostIncoming)
    
    # Add it to database session
    db.session.add(newFavorite)
    db.session.commit()
    return jsonify(newFavorite.serialize()), 200

# Delete a favorite
@app.route('/favorites/<int:position>', methods=['DELETE'])
def delete_new_favorite(position):

    # Collect data
    favorite = Favorites.query.get(position)

     # Validate data
    if favorite is None:
        raise APIException('Favorite not found', status_code=404)

    # Delete favorite
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite was deleted"}), 200

# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@app.route("/login", methods=["POST"])
def login():
    # username = request.json.get("username", None)
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = User.query.filter_by(email=email, password=password).first()
    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401
    # if username != "test" or password != "test":
    #     return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token":access_token})

# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
# @app.route("/protected", methods=["GET"])
# @jwt_required()
# def protected():
#     # Access the identity of the current user with get_jwt_identity
#     current_user = get_jwt_identity()
#     return jsonify(logged_in_as=current_user), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
