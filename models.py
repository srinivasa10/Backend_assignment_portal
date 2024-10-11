from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

mongo = PyMongo()

class User:
    @staticmethod
    def insert_user(data):
        hashed_password = generate_password_hash(data['password'])
        user_data = {
            'username': data['username'],
            'password': hashed_password,
            'role': 'user'
        }
        mongo.db.users.insert_one(user_data)
    
    @staticmethod
    def find_by_username(username):
        return mongo.db.users.find_one({"username": username})

    @staticmethod
    def authenticate(username, password):
        user = User.find_by_username(username)
        if user and check_password_hash(user['password'], password):
            return user
        return None

class Admin:
    @staticmethod
    def insert_admin(data):
        hashed_password = generate_password_hash(data['password'])
        admin_data = {
            'username': data['username'],
            'password': hashed_password,
            'role': 'admin'
        }
        mongo.db.admins.insert_one(admin_data)
    
    @staticmethod
    def find_by_username(username):
        return mongo.db.admins.find_one({"username": username})

    @staticmethod
    def authenticate(username, password):
        admin = Admin.find_by_username(username)
        if admin and check_password_hash(admin['password'], password):
            return admin
        return None

class Assignment:
    @staticmethod
    def insert_assignment(data):
        assignment_data = {
            'userId': data['userId'],
            'task': data['task'],
            'admin': data['admin'],
            'status': 'pending',
            'createdAt': data['createdAt']
        }
        mongo.db.assignments.insert_one(assignment_data)

    @staticmethod
    def get_assignments_by_admin(admin_username):
        # Fetch assignments from the database based on the admin's username
        assignments = mongo.db.assignments.find({"admin": admin_username})
        return list(assignments)  # Convert cursor to list

    @staticmethod
    def update_assignment_status(assignment_id, status):
        mongo.db.assignments.update_one(
            {"_id": assignment_id},
            {"$set": {"status": status}}
        )
