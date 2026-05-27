from src.api.config import app
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(app)