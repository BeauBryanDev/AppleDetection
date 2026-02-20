
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.db.models.users import User, UserRole
from app.db.models.farming import Orchard, Tree, YieldRecord, Image, Prediction, Detection
from app.core.security import get_password_hash


class UserFactory:
    """Factory for creating User instances for testing."""
    
    @staticmethod
    def create(
        db: Session,
        name: str = None,
        email: str = None,
        password: str = "testpass123",
        phone_number: str = None,
        role: UserRole = UserRole.FARMER,
        **kwargs
    ) -> User:
        """Create a user with default values that can be overridden."""
        import random
        
        unique_id = str(random.randint(1000, 9999))
        
        user = User(
            name=name or f"Test User {unique_id}",
            email=email or f"testuser{unique_id}@example.com",
            password_hash=get_password_hash(password),
            phone_number=phone_number or f"+57300{unique_id}",
            role=role,
            **kwargs
        )
        db.add(user)
        db.flush()
        return user
    
    @staticmethod
    def create_admin(db: Session, **kwargs) -> User:
        """Create an admin user."""
        return UserFactory.create(db, role=UserRole.ADMIN, **kwargs)


class OrchardFactory:
    """Factory for creating Orchard instances."""
    
    @staticmethod
    def create(
        db: Session,
        user: User = None,
        name: str = None,
        location: str = None,
        n_trees: int = 10,
        address: str = None,
        **kwargs
    ) -> Orchard:
        """Create an orchard with default values."""
        import random
        
        unique_id = str(random.randint(1000, 9999))
        
        if not user:
            user = UserFactory.create(db)
        
        orchard = Orchard(
            user_id=user.id,
            name=name or f"Test Orchard {unique_id}",
            location=location or f"Location {unique_id}",
            n_trees=n_trees,
            address=address or f"{unique_id} Test Street",
            **kwargs
        )
        db.add(orchard)
        db.flush()
        return orchard


class TreeFactory:
    """Factory for creating Tree instances."""
    
    @staticmethod
    def create(
        db: Session,
        orchard: Orchard = None,
        user: User = None,
        tree_code: str = None,
        tree_type: str = "Apple",
        **kwargs
    ) -> Tree:
        """Create a tree with default values."""
        import random
        
        unique_id = str(random.randint(1000, 9999))
        
        if not orchard:
            if not user:
                user = UserFactory.create(db)
            orchard = OrchardFactory.create(db, user=user)
        
        if not user:
            user = db.get(User, orchard.user_id)
        
        tree = Tree(
            user_id=user.id,
            orchard_id=orchard.id,
            tree_code=tree_code or f"TR-{unique_id}",
            tree_type=tree_type,
            **kwargs
        )
        db.add(tree)
        db.flush()
        return tree


class YieldRecordFactory:
    """Factory for creating YieldRecord instances."""
    
    @staticmethod
    def create(
        db: Session,
        user: User = None,
        filename: str = None,
        healthy_count: int = None,
        damaged_count: int = None,
        total_count: int = None,
        health_index: float = None,
        **kwargs
    ) -> YieldRecord:
        """Create a yield record with realistic defaults."""
        import random
        
        unique_id = str(uuid.uuid4())[:8]
        
        if not user:
            user = UserFactory.create(db)
        
        # Generate realistic counts
        healthy = healthy_count if healthy_count is not None else random.randint(5, 20)
        damaged = damaged_count if damaged_count is not None else random.randint(0, 5)
        total = total_count if total_count is not None else healthy + damaged
        
        if health_index is None and total > 0:
            health_index = round((healthy / total) * 100, 2)
        elif health_index is None:
            health_index = 0.0
        
        record = YieldRecord(
            user_id=user.id,
            filename=filename or f"test_image_{unique_id}.jpg",
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=health_index,
            **kwargs
        )
        db.add(record)
        db.flush()
        return record


class DetectionDataFactory:
    """Factory for creating mock detection data (not DB models)."""
    
    @staticmethod
    def create_detections(
        num_red: int = 3,
        num_green: int = 2,
        num_damaged: int = 1,
        confidence_range: tuple = (0.7, 0.95)
    ) -> Dict[str, Any]:
        """Create mock detection results for testing."""
        import random
        
        boxes = []
        class_ids = []
        confidences = []
        
        # Generate random positions
        for i in range(num_red):
            boxes.append([random.randint(10, 500), random.randint(10, 500), 
                         random.randint(30, 100), random.randint(30, 100)])
            class_ids.append(0)  # red apple
            confidences.append(round(random.uniform(*confidence_range), 2))
        
        for i in range(num_green):
            boxes.append([random.randint(10, 500), random.randint(10, 500),
                         random.randint(30, 100), random.randint(30, 100)])
            class_ids.append(2)  # green apple
            confidences.append(round(random.uniform(*confidence_range), 2))
        
        for i in range(num_damaged):
            boxes.append([random.randint(10, 500), random.randint(10, 500),
                         random.randint(30, 100), random.randint(30, 100)])
            class_ids.append(1)  # damaged apple
            confidences.append(round(random.uniform(*confidence_range), 2))
        
        healthy = num_red + num_green
        total = healthy + num_damaged
        
        return {
            "counts": {
                "red_apple": num_red,
                "green_apple": num_green,
                "healthy": healthy,
                "damaged_apple": num_damaged,
                "total": total
            },
            "detections": {
                "boxes": boxes,
                "class_ids": class_ids,
                "confidences": confidences
            }
        }
    
    @staticmethod
    def create_empty() -> Dict[str, Any]:
        """Create empty detection results."""
        return {
            "counts": {
                "red_apple": 0,
                "green_apple": 0,
                "healthy": 0,
                "damaged_apple": 0,
                "total": 0
            },
            "detections": {
                "boxes": [],
                "class_ids": [],
                "confidences": []
            }
        }


class ImageFileFactory:
    """Factory for creating mock image files."""
    
    @staticmethod
    def create_jpeg_bytes(size: int = 1024) -> bytes:
        """Create mock JPEG image bytes."""
        # Simple mock - just random bytes with JPEG header
        # In reality, you might want to use PIL to create a real tiny image
        return b'\xff\xd8\xff\xe0' + b'\x00' * (size - 4)
    
    @staticmethod
    def create_png_bytes(size: int = 1024) -> bytes:
        """Create mock PNG image bytes."""
        return b'\x89PNG\r\n\x1a\n' + b'\x00' * (size - 8)
    
    @staticmethod
    def create_test_file_tuple(
        filename: str = "test_image.jpg",
        content_type: str = "image/jpeg",
        size: int = 1024
    ) -> tuple:
        """Create a tuple suitable for FastAPI UploadFile simulation."""
        if content_type == "image/jpeg":
            content = ImageFileFactory.create_jpeg_bytes(size)
        else:
            content = ImageFileFactory.create_png_bytes(size)
        
        return (filename, content, content_type)