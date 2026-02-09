from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timedelta, timezone


def get_bogota_time():
    return datetime.now(timezone(timedelta(hours=-5)))


class YieldRecord(Base):
    __tablename__ = "yield_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String)
    healthy_count = Column(Integer)
    damaged_count = Column(Integer)
    total_count = Column(Integer)
    health_index = Column(Float)  # (healthy / total) * 100
    created_at = Column(DateTime, default=get_bogota_time)
    
    # Relationship to User
    user = relationship("User", foreign_keys=[user_id])


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
    user_id = Column(Integer, ForeignKey("users.id"))
    orchard_id = Column(Integer, ForeignKey("orchards.id"))
    tree_code = Column(String)
    tree_type = Column(String)
    
    orchard = relationship("Orchard", back_populates="trees")
    images = relationship("Image", back_populates="tree")
    
    def __repr__(self):
        return f"<Tree(id={self.id}, tree_code='{self.tree_code}')>"
    
class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    # Trazabilidad total solicitada
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    orchard_id = Column(Integer, ForeignKey("orchards.id"), nullable=False)
    tree_id = Column(Integer, ForeignKey("trees.id"), nullable=False)
    
    image_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=get_bogota_time)
    
    tree = relationship("Tree", back_populates="images")
    orchard = relationship("Orchard") # Para acceder a orchard.name
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
    
    