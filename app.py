from flask import Flask, jsonify, request
from extensions import db, migrate, jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models import User, WordList
from flask_jwt_extended import jwt_required, get_jwt_identity


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timesup.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '360c2060a5da9d1bd83dab2611500a52'  # Change this to a real secret key


db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)



@app.route('/')
def hello_world():
    return jsonify({'message': 'Hello World!'}), 200


@app.route('/test', methods=['GET'])
@jwt_required()
def test():
    return jsonify({'message': 'Test successful!'}), 200

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Username and password required"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401




@app.route('/wordlists', methods=['POST'])
@jwt_required()
def create_wordlist():
    current_user_username = get_jwt_identity()
    user = User.query.filter_by(username=current_user_username).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    title = data.get('title')
    words = data.get('words')  # Assuming words are sent as a string, e.g., "word1,word2,word3"

    if not title or not words:
        return jsonify({"msg": "Title and words are required"}), 400

    wordlist = WordList(title=title, words=words, user_id=user.id)
    db.session.add(wordlist)
    db.session.commit()

    return jsonify({"msg": "Word list created successfully", "wordlist": {"id": wordlist.id, "title": wordlist.title, "words": wordlist.words.split(",")}}), 201

@app.route('/wordlists', methods=['GET'])
@jwt_required()
def get_wordlists():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    
    wordlists = WordList.query.filter_by(user_id=user.id).all()
    
    return jsonify([{'id': wl.id, 'title': wl.title, 'words': wl.words.split(',')} for wl in wordlists]), 200


@app.route('/wordlists/<int:list_id>', methods=['PUT'])
@jwt_required()
def update_wordlist(list_id):
    current_user_username = get_jwt_identity()
    user = User.query.filter_by(username=current_user_username).first()
    wordlist = WordList.query.filter_by(id=list_id, user_id=user.id).first()

    if not wordlist:
        return jsonify({"msg": "Word list not found"}), 404

    data = request.get_json()
    words_to_add = data.get('add', [])  # A list of words to add
    words_to_remove = data.get('remove', [])  # A list of words to remove

    # Assuming words are stored as a comma-separated string in the database
    current_words_set = set(wordlist.words.split(','))

    # Add words
    current_words_set.update(words_to_add)

    # Remove words
    current_words_set.difference_update(words_to_remove)

    # Update the wordlist in the database
    wordlist.words = ','.join(current_words_set)
    db.session.commit()

    return jsonify({"msg": "Word list updated", "id": wordlist.id, "title": wordlist.title, "words": list(current_words_set)}), 200




@app.route('/wordlists/<int:list_id>', methods=['DELETE'])
@jwt_required()
def delete_wordlist(list_id):
    current_user_username = get_jwt_identity()
    user = User.query.filter_by(username=current_user_username).first()
    wordlist = WordList.query.filter_by(id=list_id, user_id=user.id).first()

    if not wordlist:
        return jsonify({"msg": "Word list not found"}), 404

    db.session.delete(wordlist)
    db.session.commit()

    return jsonify({"msg": "Word list deleted"}), 200



if __name__ == '__main__':
    app.run(debug=True)
