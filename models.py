from datetime import datetime

class User:
    def __init__(self, id, name, phone, email=None, created_at=None):
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

class Part:
    def __init__(self, id, name, category, brand, price, description, image, in_stock=True):
        self.id = id
        self.name = name
        self.category = category
        self.brand = brand
        self.price = price
        self.description = description
        self.image = image
        self.in_stock = in_stock
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'brand': self.brand,
            'price': self.price,
            'description': self.description,
            'image': self.image,
            'in_stock': self.in_stock
        }

class Order:
    def __init__(self, id, user_id, items, total_price, status='new', created_at=None):
        self.id = id
        self.user_id = user_id
        self.items = items
        self.total_price = total_price
        self.status = status
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': self.items,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

class Appointment:
    def __init__(self, id, user_id, car_brand, car_model, car_year, service_type,
                 appointment_date, appointment_time, additional_info='', status='pending', created_at=None):
        self.id = id
        self.user_id = user_id
        self.car_brand = car_brand
        self.car_model = car_model
        self.car_year = car_year
        self.service_type = service_type
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.additional_info = additional_info
        self.status = status
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'car_brand': self.car_brand,
            'car_model': self.car_model,
            'car_year': self.car_year,
            'service_type': self.service_type,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'additional_info': self.additional_info,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }