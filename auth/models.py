from __future__ import annotations
from flask_login import UserMixin
from bson import ObjectId
from pymongo.collection import Collection

class User(UserMixin):
    def __init__(self, uid: str, username: str):
        self.id = uid
        self.username = username

    @staticmethod
    def get_by_id(users_col: Collection, uid: str) -> User | None:
        doc = users_col.find_one({"_id": ObjectId(uid)})
        if doc:
            return User(str(doc["_id"]), doc["username"])
        return None
