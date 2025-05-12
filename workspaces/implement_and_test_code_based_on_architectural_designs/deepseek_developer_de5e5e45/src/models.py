# Define your database models here
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class AgentPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    success_rate = db.Column(db.Float)
    # Add more fields as needed
