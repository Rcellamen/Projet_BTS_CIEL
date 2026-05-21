from src.Api.config import app
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(app)