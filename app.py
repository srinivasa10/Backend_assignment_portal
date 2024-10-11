from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import User, Admin, Assignment, mongo
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/assignment_portal'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production

mongo.init_app(app)
jwt = JWTManager(app)

# Function to serialize ObjectId to string
def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [serialize_objectid(o) for o in obj]
    if isinstance(obj, dict):
        return {k: serialize_objectid(v) for k, v in obj.items()}
    return obj


# Welcome route
@app.route('/')
def welcome():
    return jsonify({"message": "Welcome to the Assignment Submission Portal!"}), 200

# Register user
@app.route('/register/user', methods=['POST'])
def register_user():
    data = request.get_json()
    if User.find_by_username(data['username']):
        return jsonify({"message": "User already exists"}), 400
    User.insert_user(data)
    return jsonify({"message": "User created successfully"}), 201

# Register admin
@app.route('/register/admin', methods=['POST'])
def register_admin():
    data = request.get_json()
    if Admin.find_by_username(data['username']):
        return jsonify({"message": "Admin already exists"}), 400
    Admin.insert_admin(data)
    return jsonify({"message": "Admin created successfully"}), 201

# Login user/admin
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Check in both collections: users and admins
    user = User.authenticate(data['username'], data['password']) or Admin.authenticate(data['username'], data['password'])

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user['username'])
    return jsonify(message="Login Success", access_token=access_token), 200

# Upload assignment (User only)
@app.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    current_user = get_jwt_identity()
    user = User.find_by_username(current_user)

    if not user or user['role'] != 'user':
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    data['createdAt'] = datetime.utcnow()  # Add current timestamp

    Assignment.insert_assignment(data)
    return jsonify({"message": "Assignment uploaded"}), 201

# Get list of admins
@app.route('/admins', methods=['GET'])
@jwt_required()
def get_admins():
    admins = mongo.db.admins.find({}, {"_id": 0, "username": 1})  # Fetch from admins collection
    return jsonify(list(admins)), 200

# Admin: View assignments
@app.route('/assignments', methods=['GET'])
@jwt_required()
def get_assignments():
    current_user = get_jwt_identity()
    admin = Admin.find_by_username(current_user)

    if not admin or admin['role'] != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    # Fetch assignments
    assignments = Assignment.get_assignments_by_admin(current_user)
    
    # Convert ObjectId to string for JSON serialization
    for assignment in assignments:
        assignment['_id'] = str(assignment['_id'])  # Convert ObjectId to string

    return jsonify(assignments), 200


# Admin: Accept assignment
@app.route('/assignments/<assignment_id>/accept', methods=['POST'])
@jwt_required()
def accept_assignment(assignment_id):
    current_user = get_jwt_identity()
    admin = Admin.find_by_username(current_user)

    if not admin or admin['role'] != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    Assignment.update_assignment_status(ObjectId(assignment_id), "accepted")
    return jsonify({"message": "Assignment accepted"}), 200

# Admin: Reject assignment
@app.route('/assignments/<assignment_id>/reject', methods=['POST'])
@jwt_required()
def reject_assignment(assignment_id):
    current_user = get_jwt_identity()
    admin = Admin.find_by_username(current_user)

    if not admin or admin['role'] != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    Assignment.update_assignment_status(ObjectId(assignment_id), "rejected")
    return jsonify({"message": "Assignment rejected"}), 200

if __name__ == '__main__':
    app.run(debug=True)
