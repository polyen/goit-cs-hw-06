from pymongo import MongoClient
from pymongo.server_api import ServerApi


def db():
    connection = MongoClient('mongodb://admin:root@localhost:27017/', server_api=ServerApi('1'))
    data_base = connection.messages_db.messages

    return data_base
