from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timedelta, timezone
import uuid 

from .session import Base

def get_local_datetime():
    """Returns current datetime with local timezone info"""
    return datetime.now(timezone.utc).astimezone()


class YieldRecord(Base):
    __tablename__ = "yield_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    healthy_count = Column(Integer)
    damaged_count = Column(Integer)
    total_count = Column(Integer)
    health_index = Column(Float)  # (healthy / total) * 100
    created_at = Column(DateTime, default=get_local_datetime)
    
    
class User(Base):
    
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="farmer") # farmer, admin
    created_at = Column(DateTime, default=get_local_datetime)
    
    orchards = relationship("Orchard", back_populates="owner")
    
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role='{self.role}')>"
    

class Orchard(Base):
    
    __tablename__ = "orchards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    location = Column(String)
    n_trees = Column(Integer)
    
    owner = relationship("User", back_populates="orchards")
    trees = relationship("Tree", back_populates="orchard")
    
    
    def __repr__(self):
        return f"<Orchard(id={self.id}, name='{self.name}', location='{self.location}', n_trees={self.n_trees})>"
    
class Tree(Base):
    __tablename__ = "trees"
    id = Column(Integer, primary_key=True, index=True)
    orchard_id = Column(Integer, ForeignKey("orchards.id"))
    tree_code = Column(String) # Ej: "SEC-A1-05"
    
    orchard = relationship("Orchard", back_populates="trees")
    images = relationship("Image", back_populates="tree")
    
    
    def __repr__(self):
        return f"<Tree(id={self.id}, tree_code='{self.tree_code}')>"
    

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    tree_id = Column(Integer, ForeignKey("trees.id"), nullable=True)
    image_path = Column(String, nullable=False) # URL de S3 en producción
    uploaded_at = Column(DateTime, default=get_local_datetime)
    
    tree = relationship("Tree", back_populates="images")
    prediction = relationship("Prediction", back_populates="image", uselist=False)
    
    
    def __repr__(self):
        return f"<Image(id={self.id}, image_path='{self.image_path}')>"
    

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    model_version = Column(String)
    total_apples = Column(Integer)
    good_apples = Column(Integer)
    damaged_apples = Column(Integer)
    healthy_percentage = Column(Float)
    inference_time_ms = Column(Float)
    
    image = relationship("Image", back_populates="prediction")
    detections = relationship("Detection", back_populates="prediction")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, model_version='{self.model_version}')>"
    

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"))
    class_label = Column(String)
    confidence = Column(Float)
    x_min = Column(Integer)
    y_min = Column(Integer)
    x_max = Column(Integer)
    y_max = Column(Integer)
    
    prediction = relationship("Prediction", back_populates="detections")
    
    
    def __repr__(self):
        return f"<Detection(id={self.id}, class_label='{self.class_label}', confidence={self.confidence})>"
    


