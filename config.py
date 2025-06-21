import os
from dotenv import load_dotenv

load_dotenv()  # load .env into os.environ

class Config:
    SECRET_KEY = "Yrp#[)[:VL,2(`.uk?WSaQAS1a||&@"
    MONGO_URI = "mongodb+srv://janw1990:AGt4AHnkSmER3soJ@cluster0.p2ehp7o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    # MongoClient server selection timeout (ms)
    MONGO_TIMEOUT_MS: int = 5000
