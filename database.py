"""
Database models and operations
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    language = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.now)
    
    orders = relationship("Order", back_populates="user")

class Tie(Base):
    __tablename__ = 'ties'
    
    id = Column(Integer, primary_key=True)
    name_ru = Column(String(200), nullable=False)
    name_kz = Column(String(200))
    name_en = Column(String(200))
    color_ru = Column(String(100))
    color_kz = Column(String(100))
    color_en = Column(String(100))
    material_ru = Column(String(100), default='100% натуральный материал')
    material_kz = Column(String(100), default='100% табиғи материал')
    material_en = Column(String(100), default='100% natural material')
    description_ru = Column(Text)
    description_kz = Column(Text)
    description_en = Column(Text)
    price = Column(Float, nullable=False)
    image_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(Integer, ForeignKey('users.telegram_id'))
    tie_id = Column(Integer, ForeignKey('ties.id'))
    tie_name = Column(String(200))
    price = Column(Float)
    recipient_name = Column(String(100))
    recipient_surname = Column(String(100))
    recipient_phone = Column(String(20))
    delivery_address = Column(Text)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="orders")
    tie = relationship("Tie")

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tie_shop.db')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_or_create_user(telegram_id: int, username: str = None) -> User:
    """Get existing user or create new one"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            session.commit()
        return user
    finally:
        session.close()

def update_user_language(telegram_id: int, language: str):
    """Update user language preference"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.language = language
            session.commit()
    finally:
        session.close()

def get_user_language(telegram_id: int) -> str:
    """Get user language preference"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user.language if user else None
    finally:
        session.close()

def migrate_ties_from_json():
    """Migrate ties from JSON file to database"""
    import json
    session = Session()
    try:
        # Check if ties already exist
        if session.query(Tie).count() > 0:
            return
        
        # Load ties from JSON
        with open('ties_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create ties in database
        for tie_data in data['ties']:
            tie = Tie(
                name_ru=tie_data['name'].get('ru', ''),
                name_kz=tie_data['name'].get('kz', ''),
                name_en=tie_data['name'].get('en', ''),
                color_ru=tie_data['color'].get('ru', ''),
                color_kz=tie_data['color'].get('kz', ''),
                color_en=tie_data['color'].get('en', ''),
                material_ru=tie_data['material'].get('ru', '100% натуральный материал'),
                material_kz=tie_data['material'].get('kz', '100% табиғи материал'),
                material_en=tie_data['material'].get('en', '100% natural material'),
                description_ru=tie_data['description'].get('ru', ''),
                description_kz=tie_data['description'].get('kz', ''),
                description_en=tie_data['description'].get('en', ''),
                price=tie_data.get('price', 1500),
                image_path=tie_data.get('image', ''),
                is_active=True
            )
            session.add(tie)
        
        session.commit()
        print(f"Migrated {len(data['ties'])} ties to database")
    except Exception as e:
        print(f"Error migrating ties: {e}")
        session.rollback()
    finally:
        session.close()

def get_all_active_ties():
    """Get all active ties from database"""
    session = Session()
    try:
        return session.query(Tie).filter_by(is_active=True).all()
    finally:
        session.close()

def get_tie_by_id(tie_id: int):
    """Get tie by ID"""
    session = Session()
    try:
        return session.query(Tie).filter_by(id=tie_id).first()
    finally:
        session.close()

def create_tie(name_ru, color_ru, price, description_ru, image_path=None):
    """Create new tie"""
    session = Session()
    try:
        tie = Tie(
            name_ru=name_ru,
            name_kz=name_ru,  # Default to Russian
            name_en=name_ru,
            color_ru=color_ru,
            color_kz=color_ru,
            color_en=color_ru,
            description_ru=description_ru,
            description_kz=description_ru,
            description_en=description_ru,
            price=price,
            image_path=image_path,
            is_active=True
        )
        session.add(tie)
        session.commit()
        return tie.id
    finally:
        session.close()

def update_tie(tie_id, **kwargs):
    """Update tie fields"""
    print(f"=== UPDATE_TIE START ===")
    print(f"Updating tie {tie_id} with fields: {kwargs}")
    session = Session()
    try:
        tie = session.query(Tie).filter_by(id=tie_id).first()
        if tie:
            print(f"Found tie: {tie.name_ru}, current price: {tie.price}")
            for key, value in kwargs.items():
                if hasattr(tie, key):
                    print(f"Setting {key} = {value} (was: {getattr(tie, key)})")
                    setattr(tie, key, value)
                else:
                    print(f"WARNING: Tie has no attribute {key}")
            print(f"Before commit - tie price: {tie.price}")
            session.commit()
            print(f"After commit - tie price: {tie.price}")
            print(f"Successfully updated tie {tie_id}")
            return True
        else:
            print(f"Tie with ID {tie_id} not found")
        return False
    except Exception as e:
        print(f"Error updating tie {tie_id}: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()
        print(f"=== UPDATE_TIE END ===")

def delete_tie(tie_id):
    """Soft delete tie (mark as inactive)"""
    session = Session()
    try:
        tie = session.query(Tie).filter_by(id=tie_id).first()
        if tie:
            tie.is_active = False
            session.commit()
            return True
        return False
    finally:
        session.close()

def create_order(order_data: dict) -> Order:
    """Create a new order"""
    session = Session()
    try:
        order = Order(**order_data)
        session.add(order)
        session.commit()
        # Refresh to get the ID
        session.refresh(order)
        # Return the order object
        return order
    finally:
        session.close()

def get_user_orders(telegram_id: int) -> list:
    """Get all orders for a user"""
    session = Session()
    try:
        orders = session.query(Order).filter_by(user_telegram_id=telegram_id).all()
        return orders
    finally:
        session.close()

def get_tie_by_id(tie_id):
    """Получить товар по ID"""
    session = Session()
    try:
        tie = session.query(Tie).filter(Tie.id == tie_id).first()
        return tie
    finally:
        session.close()

def create_tie(tie_data):
    """Создать новый товар"""
    session = Session()
    try:
        tie = Tie(
            name_ru=tie_data.get('name_ru'),
            name_kz=tie_data.get('name_kz'),
            name_en=tie_data.get('name_en'),
            color_ru=tie_data.get('color_ru'),
            color_kz=tie_data.get('color_kz'),
            color_en=tie_data.get('color_en'),
            material_ru=tie_data.get('material_ru', '100% натуральный материал'),
            material_kz=tie_data.get('material_kz', '100% табиғи материал'),
            material_en=tie_data.get('material_en', '100% natural material'),
            description_ru=tie_data.get('description_ru'),
            description_kz=tie_data.get('description_kz'),
            description_en=tie_data.get('description_en'),
            price=tie_data.get('price'),
            image_path=tie_data.get('image_path'),
            is_active=tie_data.get('is_active', True)
        )
        session.add(tie)
        session.commit()
        return tie
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def toggle_tie_status(tie_id):
    """Переключить статус товара (активен/неактивен)"""
    session = Session()
    try:
        tie = session.query(Tie).filter(Tie.id == tie_id).first()
        if not tie:
            return None
        
        tie.is_active = not tie.is_active
        session.commit()
        return tie
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def update_order_status(order_id: int, status: str):
    """Update order status"""
    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = status
            session.commit()
    finally:
        session.close()

def get_order_by_id(order_id: int) -> Order:
    """Get order by ID"""
    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        return order
    finally:
        session.close()

def clear_all_data():
    """Clear all data from database - for production launch"""
    session = Session()
    try:
        # Clear all orders
        session.query(Order).delete()
        
        # Clear all users
        session.query(User).delete()
        
        # Keep ties as they are - don't modify catalog
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error clearing database: {e}")
        return False
    finally:
        session.close()

def reset_ties_to_default():
    """Reset ties to default state from JSON"""
    session = Session()
    try:
        # First clear all ties
        session.query(Tie).delete()
        session.commit()
        
        # Re-migrate from JSON
        migrate_json_to_db()
        
        return True
    except Exception as e:
        session.rollback()
        print(f"Error resetting ties: {e}")
        return False
    finally:
        session.close()
