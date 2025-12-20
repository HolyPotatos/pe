import os
import hashlib

def password_hash(password, salt = None):
    if salt is None:
        salt = os.urandom(16)
        return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,100000), salt
    return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,100000)

def password_check(stored_hash, stored_salt, password):
    check_hash = password_hash(password, stored_salt)
    return check_hash == stored_hash