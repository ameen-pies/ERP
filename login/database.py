# -*- coding: utf-8 -*-
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB configuration - FIXED to match .env variable names
MONGODB_URI = os.getenv('MONGODB_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'purchase_request')
USERS_COLLECTION = os.getenv('USERS_COLLECTION', 'users_login_signup')

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DB_NAME]
    users_collection = db[USERS_COLLECTION]
    print(f"✅ Connected to MongoDB successfully!")
    print(f"📁 Database: {MONGO_DB_NAME}")
    print(f"📊 Collection: {USERS_COLLECTION}")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None
    db = None
    users_collection = None


def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_user(fullname, email, department, role, password):
    """Create a new user in the database"""
    try:
        print(f"Attempting to create user: {email}")
        print(f"Target: {MONGO_DB_NAME}.{USERS_COLLECTION}")
        
        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            print(f"User already exists: {email}")
            return {"success": False, "message": "Email already exists"}
        
        # Hash the password
        hashed_password = hash_password(password)
        print(f"Password hashed successfully")
        
        # Create user document
        user_doc = {
            "full_name": fullname,
            "email": email,
            "password_hash": hashed_password,
            "department": department,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        result = users_collection.insert_one(user_doc)
        print(f"User created successfully with ID: {result.inserted_id}")
        print(f"Saved to: {MONGO_DB_NAME}.{USERS_COLLECTION}")
        
        return {
            "success": True,
            "message": "User created successfully",
            "user_id": str(result.inserted_id)
        }
    
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return {"success": False, "message": f"Error creating user: {str(e)}"}


def authenticate_user(email, password):
    """Authenticate a user with email and password"""
    try:
        print(f"Attempting to authenticate user: {email}")
        print(f"Searching in: {MONGO_DB_NAME}.{USERS_COLLECTION}")
        
        # Find user by email
        user = users_collection.find_one({"email": email})
        
        if not user:
            print(f"User not found: {email}")
            return {"success": False, "message": "Invalid email or password"}
        
        # Check if user is active
        if not user.get("is_active", True):
            print(f"User account is inactive: {email}")
            return {"success": False, "message": "Account is inactive"}
        
        # Verify password
        if verify_password(password, user["password_hash"]):
            print(f"Authentication successful for: {email}")
            # Remove password hash from returned user data
            user.pop("password_hash", None)
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
            
            return {
                "success": True,
                "message": "Authentication successful",
                "user": user
            }
        else:
            print(f"Invalid password for: {email}")
            return {"success": False, "message": "Invalid email or password"}
    
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return {"success": False, "message": f"Error during authentication: {str(e)}"}


def get_user_by_email(email):
    """Get user information by email"""
    try:
        user = users_collection.find_one({"email": email})
        if user:
            user.pop("password_hash", None)
            user["_id"] = str(user["_id"])
            return {"success": True, "user": user}
        return {"success": False, "message": "User not found"}
    except Exception as e:
        return {"success": False, "message": f"Error fetching user: {str(e)}"}


def update_user(email, update_data):
    """Update user information"""
    try:
        result = users_collection.update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "User updated successfully"}
        return {"success": False, "message": "No changes made or user not found"}
    
    except Exception as e:
        return {"success": False, "message": f"Error updating user: {str(e)}"}


def delete_user(email):
    """Delete a user (soft delete by setting is_active to False)"""
    try:
        result = users_collection.update_one(
            {"email": email},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "User deactivated successfully"}
        return {"success": False, "message": "User not found"}
    
    except Exception as e:
        return {"success": False, "message": f"Error deactivating user: {str(e)}"}