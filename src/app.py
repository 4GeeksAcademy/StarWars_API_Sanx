"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
#from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, FavoritePlanet, FavoriteCharacter
from sqlalchemy import select

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

#usuarios
@app.route('/users', methods=['GET'])
def get_all_users():

    stmt=select(User)
    all_users = db.session.execute(stmt).scalars().all()
    all_users = list(map(lambda item: item.serialize(), all_users))

    return jsonify(all_users),200

#GestionGlobalfavoritos
@app.route('/users/<int:user_id>/favorites', methods=['GET'])

def get_favorite(user_id):
    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return { 'message': f"El usuario con el id {user_id} no existe"},404
    
    array_planet = []
    for planet in user.FavoritePlanet:
        array_planet.append(planet.serialize())
    
    array_character = []
    for character in user.FavoriteCharacter:
        array_character.append(character.serialize())


    return {'user_id': user_id, "favorites":{"planets": array_planet, 'characters': array_character}}, 200

#pjs
@app.route('/people', methods=['GET'])
def get_all_characters():

    stmt=select(Character)
    all_characters = db.session.execute(stmt).scalars().all()
    serialized_characters = list(map(lambda item: item.serialize(), all_characters))
    return jsonify(serialized_characters), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_character(people_id):
    character = db.session.execute(select(Character).where(Character.id == people_id)).scalar_one_or_none()
    
    if character is None:
        return {'message': f"El personaje con el id {people_id} no existe"}, 404
    
    return jsonify(character.serialize()), 200

@app.route('/people', methods=['POST'])
def create_character():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No se proporcionaron datos para crear el personaje"}), 400
    
    required_fields = ['name', 'age', 'genre', 'affiliation']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Faltan campos obligatorios: name, age, genre, affiliation"}), 400
    
    existing_character = db.session.execute(select(Character).where(Character.name == data['name'])).scalar_one_or_none()
    if existing_character:
        return jsonify({"message": f"Ya existe un personaje con el nombre '{data['name']}'"}), 409

    new_character = Character(
        name=data['name'],
        age=data['age'],
        genre=data['genre'],
        affiliation=data['affiliation']
    )
    db.session.add(new_character)
    db.session.commit()
    
    return jsonify(new_character.serialize()), 201

@app.route('/people/<int:people_id>', methods=['PUT'])
def modify_character(people_id):
    
    data = request.get_json()

    if not data:
        return jsonify({"message": "No se proporcionaron datos para actualizar"}), 400

    character = db.session.execute(select(Character).where(Character.id == people_id)).scalar_one_or_none()
    if character is None:
        return {'message': f"El personaje con el id {people_id} no existe"}, 404

    if 'name' in data:
        character.name = data['name']
    if 'age' in data:
        character.age = data['age']
    if 'genre' in data:
        character.genre = data['genre']
    if 'affiliation' in data:
        character.affiliation = data['affiliation']

    db.session.commit()

    return jsonify(character.serialize()), 200

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_character(people_id):
    character = db.session.execute(select(Character).where(Character.id == people_id)).scalar_one_or_none()
    if character is None:
        return {'message': f"El personaje con el id {people_id} no existe"}, 404
    
    db.session.delete(character)
    db.session.commit()
    
    return jsonify({'message': f"Personaje con id {people_id} eliminado exitosamente"}), 200

#pjsfavoritos
@app.route('/users/<int:user_id>/favorite/people/<int:people_id>', methods=['POST'])

def post_character_favorite(user_id, people_id):
    character = db.session.execute(select(Character).where(Character.id == people_id)).scalar_one_or_none()
    if character is None:
        return { 'message': f"El personaje con el id {people_id} no existe"}, 404

    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return { 'message': f"El usuario con el id {user_id} no existe"}, 404
    
    if character in user.FavoriteCharacter:
        return {'message': f"El personaje con id {people_id} ya es favorito del usuario {user_id}"}, 409

    user.FavoriteCharacter.append(character)

    db.session.commit()
    
    return jsonify({'message': f"Personaje con id {people_id} añadido a favoritos del usuario {user_id}"}), 201

@app.route('/users/<int:user_id>/favorite/people/<int:people_id>', methods=['DELETE'])

def delete_character_favorite(user_id, people_id):
    character = db.session.execute(select(Character).where(Character.id == people_id)).scalar_one_or_none()
    if character is None:
        return { 'message': f"El personaje con el id {people_id} no existe"}, 404
    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return { 'message': f"El usuario con el id {user_id} no existe"}, 404
    
    if character not in user.FavoriteCharacter:
        return {'message': f"El personaje con id {people_id} no es favorito de {user_id}"}, 400
    
    user.FavoriteCharacter.remove(character)

    db.session.commit()

    return jsonify({'message': f"Favorito eliminado exitosamente"}), 200

#planetas
@app.route('/planets', methods=['GET'])
def get_all_planets():
    stmt = select(Planet)
    all_planets = db.session.execute(stmt).scalars().all()
    serialized_planets = list(map(lambda item: item.serialize(), all_planets))
    return jsonify(serialized_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET']) 
def get_planet(planet_id):
    planet = db.session.execute(select(Planet).where(Planet.id == planet_id)).scalar_one_or_none()
    
    if planet is None:
        return {'message': f"El planeta con el id {planet_id} no existe"}, 404 
    
    return jsonify(planet.serialize()), 200

@app.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No se proporcionaron datos para crear el planeta"}), 400
    
    required_fields = ['name', 'size', 'material', 'population']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Faltan campos obligatorios: name, size, material, population"}), 400

    existing_planet = db.session.execute(select(Planet).where(Planet.name == data['name'])).scalar_one_or_none()
    if existing_planet:
        return jsonify({"message": f"Ya existe un planeta con el nombre '{data['name']}'"}), 409 

    new_planet = Planet(
        name=data['name'],
        size=data['size'],
        material=data['material'],
        population=data['population']
    )
    db.session.add(new_planet)
    db.session.commit()
    
    return jsonify(new_planet.serialize()), 201 


@app.route('/planets/<int:planet_id>', methods=['PUT'])
def modify_planet(planet_id):

    data = request.get_json()

    if not data:
        return jsonify({"message": "No se proporcionaron datos para actualizar"}), 400

    planet = db.session.execute(select(Planet).where(Planet.id == planet_id)).scalar_one_or_none()
    if planet is None:
        return {'message': f"El planeta con el id {planet_id} no existe"}, 404
    
    if 'name' in data:
        planet.name = data['name']
    if 'size' in data:
        planet.size = data['size']
    if 'material' in data:
        planet.material = data['material']
    if 'population' in data:
        planet.population = data['population']

    db.session.commit()

    return jsonify(planet.serialize()), 200

@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = db.session.execute(select(Planet).where(Planet.id == planet_id)).scalar_one_or_none()
    if planet is None:
        return {'message': f"El planeta con el id {planet_id} no existe"}, 404
    
    db.session.delete(planet)
    db.session.commit()
    
    return jsonify({'message': f"Planeta con id {planet_id} eliminado exitosamente"}), 200

#planetas favoritos
@app.route('/users/<int:user_id>/favorite/planet/<int:planet_id>', methods=['POST'])

def post_planet_favorite(user_id, planet_id):
    planet = db.session.execute(select(Planet).where(Planet.id == planet_id)).scalar_one_or_none()
    if planet is None:
        return { 'message': f"El planeta con el id {planet_id} no existe"}, 404

    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return { 'message': f"El usuario con el id {user_id} no existe"}, 404
    
    if planet in user.FavoritePlanet:
        return {'message': f"El planeta con id {planet_id} ya es favorito del usuario {user_id}"}, 409

    user.FavoritePlanet.append(planet)

    db.session.commit()
    
    return jsonify({'message': f"Planeta con id {planet_id} añadido a favoritos del usuario {user_id}"}), 201
    

@app.route('/users/<int:user_id>/favorite/planet/<int:planet_id>', methods=['DELETE'])

def delete_planet_favorite(user_id, planet_id):
    planet = db.session.execute(select(Planet).where(Planet.id == planet_id)).scalar_one_or_none()
    if planet is None:
        return { 'message': f"El planeta con el id {planet_id} no existe"}, 404
    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return { 'message': f"El usuario con el id {user_id} no existe"}, 404
    
    if planet not in user.FavoritePlanet:
        return {'message': f"El planeta con id {planet_id} no es favorito de {user_id}"}, 400
    
    user.FavoritePlanet.remove(planet)

    db.session.commit()

    return jsonify({'message': f"Favorito eliminado exitosamente"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
