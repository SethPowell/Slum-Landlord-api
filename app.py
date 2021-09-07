from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://hvjgxdfiotwggc:1c73534dcde0556e256e9ac288cc6ca0c44f34ba0048d487f908ff0663a661a7@ec2-54-145-188-92.compute-1.amazonaws.com:5432/d8vhh2fq8uufnq"

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    existing_game = db.Column(db.Boolean, nullable=False)
    money = db.Column(db.Float, nullable=False)
    tokens = db.relationship("Token", backref="user", cascade="all, delete, delete-orphan")

    def __init__(self, username, password, money=1): 
        self.username = username
        self.password = password
        self.existing_game = False
        self.money = money


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, name, user_id): 
        self.name = name
        self.user_id = user_id


class TokenSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "user_id")

token_schema = TokenSchema()
multiple_token_schema = TokenSchema(many=True)


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password", "existing_game", "money", "tokens") # Normally you wouldn't include password or anything sensitive
    tokens= ma.Nested(multiple_token_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

# USER ENDPOINTS

@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data for add_user must be sent as json")
    
    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")
    money = post_data.get("money", 0)

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    new_record = User(username, pw_hash, money)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(user_schema.dump(new_record))

@app.route("/user/verification", methods=["POST"])
def verification():
    if request.content_type != "application/json":
        return jsonify("Error: Data for verification must be sent as json")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify("Unable to verify user credentials")

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify("Unable to verify user credentials")

    return jsonify(user_schema.dump(user))

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))

@app.route("/user/get/<username>", methods=["GET"])
def get_user(username):
    user = db.session.query(User).filter(User.username == username).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/update/<id>", methods=["PUT"])
def update_user(id):
    if request.content_type != "application/json":
        return jsonify("Error: Data for update_user must be sent as json")

    money = request.json.get("money")
    existing_game = request.json.get("existing_game")
    user = db.session.query(User).filter(User.id == id).first()

    user.existing_game = existing_game
    user.money = money
    db.session.commit()

    return jsonify(user_schema.dump(user))


# TOKEN ENDPOINTS

@app.route("/token/add", methods=["POST"])
def add_token():
    if request.content_type != "application/json":
        return jsonify("Error: Data for add_token must be sent as json")
    
    post_data = request.get_json()
    name = post_data.get("name")
    user_id = post_data.get("user_id")

    new_record = Token(name, user_id)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(token_schema.dump(new_record))

@app.route("/token/get", methods=["GET"])
def get_all_tokens():
    all_tokens = db.session.query(Token).all()
    return jsonify(multiple_token_schema.dump(all_tokens))

@app.route("/token/get/<id>", methods=["GET"])
def get_token(id):
    token = db.session.query(Token).filter(Token.id == id).first()
    return jsonify(token_schema.dump(token))

@app.route("/token/delete/<user_id>", methods=["DELETE"])
def delete_tokens(user_id):
    tokens = db.session.query(Token).filter(Token.user_id == user_id).all()

    for token in tokens:
        db.session.delete(token)
        db.session.commit()

    user = db.session.query(User).filter(User.id == user_id).first()

    return jsonify(user_schema.dump(user))



# always goes at the end
if __name__ == "__main__":
    app.run(debug=True)