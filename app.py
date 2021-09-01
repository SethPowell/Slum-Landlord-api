from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://hvjgxdfiotwggc:1c73534dcde0556e256e9ac288cc6ca0c44f34ba0048d487f908ff0663a661a7@ec2-54-145-188-92.compute-1.amazonaws.com:5432/d8vhh2fq8uufnq"

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    money = db.Column(db.Float, nullable=False)
    tokens = db.relationship("Token", backref="user", cascade="all, delete, delete-orphan")

    def __init__(self, username, password, money=1): 
        self.username = username
        self.password = password
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
        fields = ("id", "username", "password", "money", "tokens") # Normally you wouldn't include password or anything sensitive
    tokens= ma.Nested(multiple_token_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)


@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data for add_user must be sent as json")
    
    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")
    money = post_data.get("money", 0)

    new_record = User(username, password, money)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(user_schema.dump(new_record))

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))

@app.route("/user/get/<username>", methods=["GET"])
def get_user(username):
    user = db.session.query(User).filter(User.username == username).first()
    return jsonify(user_schema.dump(user))

# always goes at the end
if __name__ == "__main__":
    app.run(debug=True)