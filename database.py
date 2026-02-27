import os
import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='autoservice.db'):
        # Указываем полный путь к базе данных
        self.db_name = r'C:\Users\dimka\OneDrive\Desktop\proj\kursach\autoservice.db'
        
        # Создаем папку если её нет
        db_dir = os.path.dirname(self.db_name)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Создана папка: {db_dir}")
        
        print(f"База данных будет создана по пути: {self.db_name}")
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица запчастей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                image TEXT,
                in_stock BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_data TEXT NOT NULL,
                total_price INTEGER NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица записей на ТО
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                car_brand TEXT NOT NULL,
                car_model TEXT NOT NULL,
                car_year INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TEXT NOT NULL,
                additional_info TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица автомобилей пользователя
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                vin TEXT,
                license_plate TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица сообщений чата
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                message TEXT NOT NULL,
                is_support BOOLEAN DEFAULT 0,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("База данных успешно инициализирована")
    
    # ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========
    
    def get_or_create_user(self, name, phone, email=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем существующего пользователя
        cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
        user = cursor.fetchone()
        
        if user:
            conn.close()
            return {'id': user[0], 'name': user[1], 'phone': user[2], 'email': user[3]}
        else:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (name, phone, email)
                VALUES (?, ?, ?)
            ''', (name, phone, email))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'id': user_id, 'name': name, 'phone': phone, 'email': email}
    
    def update_user_profile(self, user_id, name, email):
        """Обновление профиля пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET name = ?, email = ?
            WHERE id = ?
        ''', (name, email, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    # ========== РАБОТА С ЗАПЧАСТЯМИ ==========
    
    def init_parts_data(self):
        """Инициализация тестовых данных запчастей"""
        parts = [
            # Масла и фильтры
            {'name': 'Масло моторное 5W-40', 'category': 'oil', 'brand': 'toyota', 'price': 2500, 
             'description': 'Синтетическое масло 4л', 'image': 'https://avatars.mds.yandex.net/i?id=fdd825d05eb78862c718eab167b693570bcab7c4-5468635-images-thumbs&n=13'},
            {'name': 'Масляный фильтр', 'category': 'oil', 'brand': 'toyota', 'price': 500, 
             'description': 'Оригинальный фильтр', 'image': 'https://avatars.mds.yandex.net/get-mpic/5068955/img_id6275696105675606823.jpeg/orig'},
            {'name': 'Воздушный фильтр', 'category': 'oil', 'brand': 'nissan', 'price': 800, 
             'description': 'Фильтр двигателя', 'image': 'https://emex.ru/Find2/Find/GetDetailImage?detailKey=7avt6muxjgrb69uxtafn6jkxtdrv69wx8aywhwf3jdvr2uq&detailImageId=2869336'},
            
            # Тормозная система
            {'name': 'Тормозные колодки передние', 'category': 'brake', 'brand': 'hyundai', 'price': 3200, 
             'description': 'Комплект на 2 колеса', 'image': 'https://avatars.mds.yandex.net/get-mpic/4696638/2a00000194639246fcf144ec35b742fbc400/orig'},
            {'name': 'Тормозные диски', 'category': 'brake', 'brand': 'kia', 'price': 4500, 
             'description': 'Вентилируемые', 'image': 'https://main-cdn.sbermegamarket.ru/big1/hlr-system/926/894/299/361/837/100039492247b0.jpg'},
            {'name': 'Тормозная жидкость DOT-4', 'category': 'brake', 'brand': 'all', 'price': 600, 
             'description': '1 литр', 'image': 'https://avatars.mds.yandex.net/get-marketpic/7741417/pic2ebd8d3da72c61bd7e64e55ddd30ab61/orig'},
            
            # Двигатель
            {'name': 'Ремень ГРМ', 'category': 'engine', 'brand': 'toyota', 'price': 3800, 
             'description': 'Комплект с роликами', 'image': 'https://avatars.mds.yandex.net/get-mpic/4055794/img_id651118449483376700.jpeg/orig'},
            {'name': 'Свечи зажигания', 'category': 'engine', 'brand': 'bmw', 'price': 2200, 
             'description': 'Комплект 4 шт', 'image': 'https://basket-27.wbbasket.ru/vol4975/part497501/497501850/images/big/1.webp'},
            {'name': 'Помпа водяная', 'category': 'engine', 'brand': 'renault', 'price': 3500, 
             'description': 'Насос охлаждения', 'image': 'https://avatars.mds.yandex.net/get-mpic/11472827/2a0000018f39a6c8e2131b9bdde678a32f9a/orig'},
            
            # Подвеска
            {'name': 'Амортизатор передний', 'category': 'suspension', 'brand': 'toyota', 'price': 5500, 
             'description': 'Масляный', 'image': 'https://avatars.mds.yandex.net/get-mpic/15584819/2a0000019a540373cc2e2efa8eb7871b57e2/orig'},
            {'name': 'Шаровая опора', 'category': 'suspension', 'brand': 'nissan', 'price': 1500, 
             'description': 'Нижняя', 'image': 'https://ir.ozone.ru/s3/multimedia-1-p/7809046621.jpg'},
            {'name': 'Сайлентблок', 'category': 'suspension', 'brand': 'hyundai', 'price': 900, 
             'description': 'Переднего рычага', 'image': 'https://avatars.mds.yandex.net/get-mpic/11482776/2a0000018bf7cf49ed7ee0937f972180ea32/orig'},
            
            # Электрика
            {'name': 'Аккумулятор 60Ah', 'category': 'electrics', 'brand': 'all', 'price': 6500, 
             'description': 'Необслуживаемый', 'image': 'https://avatars.mds.yandex.net/get-mpic/12301852/2a0000018c58035fef0184cbe84e7fed12d7/orig'},
            {'name': 'Генератор', 'category': 'electrics', 'brand': 'kia', 'price': 8500, 
             'description': 'Новый', 'image': 'https://avatars.mds.yandex.net/get-mpic/11312687/2a0000018b18fd9f4ea3621469692d6c539b/orig'},
            {'name': 'Стартер', 'category': 'electrics', 'brand': 'toyota', 'price': 7800, 
             'description': 'Оригинал', 'image': 'https://ir.ozone.ru/s3/multimedia-m/c600/6261474970.jpg'},
            
            # Кузовные детали
            {'name': 'Фара левая', 'category': 'bodywork', 'brand': 'toyota', 'price': 12000, 
             'description': 'Светодиодная', 'image': 'https://avatars.mds.yandex.net/get-mpic/4303817/2a000001963eee0882b90197e4a9bf9b475e/orig'},
            {'name': 'Бампер передний', 'category': 'bodywork', 'brand': 'nissan', 'price': 15000, 
             'description': 'В цвет', 'image': 'https://basket-17.wbbasket.ru/vol2834/part283493/283493864/images/big/1.webp'},
            {'name': 'Зеркало боковое', 'category': 'bodywork', 'brand': 'hyundai', 'price': 4500, 
             'description': 'С подогревом', 'image': 'https://avatars.mds.yandex.net/get-mpic/4250892/img_id8865515304351179951.jpeg/orig'}
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже данные
        cursor.execute('SELECT COUNT(*) FROM parts')
        count = cursor.fetchone()[0]
        
        if count == 0:
            for part in parts:
                cursor.execute('''
                    INSERT INTO parts (name, category, brand, price, description, image, in_stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (part['name'], part['category'], part['brand'], part['price'], 
                      part['description'], part['image'], 1))
        
        conn.commit()
        conn.close()
    
    def get_all_parts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parts ORDER BY id')
        parts = cursor.fetchall()
        conn.close()
        
        return [{
            'id': p[0],
            'name': p[1],
            'category': p[2],
            'brand': p[3],
            'price': p[4],
            'description': p[5],
            'image': p[6],
            'in_stock': bool(p[7])
        } for p in parts]
    
    def get_part_by_id(self, part_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parts WHERE id = ?', (part_id,))
        p = cursor.fetchone()
        conn.close()
        
        if p:
            return {
                'id': p[0],
                'name': p[1],
                'category': p[2],
                'brand': p[3],
                'price': p[4],
                'description': p[5],
                'image': p[6],
                'in_stock': bool(p[7])
            }
        return None
    
    # ========== РАБОТА С ЗАКАЗАМИ ==========
    
    def create_order(self, user_id, items, total_price):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        order_data = json.dumps(items, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO orders (user_id, order_data, total_price, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, order_data, total_price, 'new'))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return order_id
    
    def get_user_orders(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        
        result = []
        for o in orders:
            result.append({
                'id': o[0],
                'user_id': o[1],
                'items': json.loads(o[2]),
                'total_price': o[3],
                'status': o[4],
                'created_at': o[5]
            })
        return result
    
    # ========== РАБОТА С ЗАПИСЯМИ ==========
    
    def create_appointment(self, user_id, appointment_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointments 
            (user_id, car_brand, car_model, car_year, service_type, 
             appointment_date, appointment_time, additional_info, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            appointment_data['carBrand'],
            appointment_data['carModel'],
            appointment_data['carYear'],
            appointment_data['serviceType'],
            appointment_data['date'],
            appointment_data['time'],
            appointment_data.get('additionalInfo', ''),
            'pending'
        ))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return appointment_id
    
    def get_user_appointments(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM appointments 
            WHERE user_id = ? 
            ORDER BY appointment_date DESC, appointment_time DESC
        ''', (user_id,))
        appointments = cursor.fetchall()
        conn.close()
        
        result = []
        for a in appointments:
            result.append({
                'id': a[0],
                'user_id': a[1],
                'car_brand': a[2],
                'car_model': a[3],
                'car_year': a[4],
                'service_type': a[5],
                'appointment_date': a[6],
                'appointment_time': a[7],
                'additional_info': a[8],
                'status': a[9],
                'created_at': a[10]
            })
        return result
    
    def cancel_appointment(self, appointment_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM appointments 
            WHERE id = ? AND user_id = ? AND status = 'pending'
        ''', (appointment_id, user_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    # ========== РАБОТА С АВТОМОБИЛЯМИ ПОЛЬЗОВАТЕЛЯ ==========
    
    def add_user_car(self, user_id, car_data):
        """Добавление автомобиля пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_cars (user_id, brand, model, year, vin, license_plate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            car_data.get('brand'),
            car_data.get('model'),
            car_data.get('year'),
            car_data.get('vin'),
            car_data.get('license_plate')
        ))
        
        car_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return car_id
    
    def get_user_cars(self, user_id):
        """Получение всех автомобилей пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_cars 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        cars = cursor.fetchall()
        conn.close()
        
        return [{
            'id': car[0],
            'user_id': car[1],
            'brand': car[2],
            'model': car[3],
            'year': car[4],
            'vin': car[5],
            'license_plate': car[6],
            'created_at': car[7]
        } for car in cars]
    
    def delete_user_car(self, car_id, user_id):
        """Удаление автомобиля пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_cars 
            WHERE id = ? AND user_id = ?
        ''', (car_id, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    # ========== РАБОТА С ЧАТОМ ==========

    def save_chat_message(self, user_id, user_name, message, is_support=False):
        """Сохранение сообщения чата"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_messages (user_id, user_name, message, is_support)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, message, is_support))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id

    def get_chat_history(self, user_id, limit=50):
        """Получение истории чата пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_messages 
            WHERE user_id = ? 
            ORDER BY created_at ASC
            LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        return [{
            'id': m[0],
            'user_id': m[1],
            'user_name': m[2],
            'message': m[3],
            'is_support': bool(m[4]),
            'is_read': bool(m[5]),
            'created_at': m[6]
        } for m in messages]

    def get_unread_messages(self, user_id):
        """Получение непрочитанных сообщений"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM chat_messages 
            WHERE user_id = ? AND is_support = 1 AND is_read = 0
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def mark_messages_as_read(self, user_id):
        """Отметить сообщения как прочитанные"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_messages 
            SET is_read = 1 
            WHERE user_id = ? AND is_support = 1 AND is_read = 0
        ''', (user_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected