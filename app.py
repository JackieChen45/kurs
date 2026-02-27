from flask import Flask, render_template, request, jsonify, session
from database import Database
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-12345'  # Измените на свой секретный ключ
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Инициализация базы данных
db = Database()
db.init_parts_data()  # Заполняем тестовыми данными

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_current_user():
    """Получение текущего пользователя из сессии"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return {
        'id': user_id, 
        'name': session.get('user_name'), 
        'phone': session.get('user_phone'),
        'email': session.get('user_email')
    }

# ========== МАРШРУТЫ ДЛЯ СТРАНИЦ ==========

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

# ========== API ДЛЯ РАБОТЫ С КАТАЛОГОМ ==========

@app.route('/api/parts', methods=['GET'])
def get_parts():
    """Получение всех запчастей"""
    parts = db.get_all_parts()
    return jsonify({'success': True, 'parts': parts})

@app.route('/api/parts/<int:part_id>', methods=['GET'])
def get_part(part_id):
    """Получение запчасти по ID"""
    part = db.get_part_by_id(part_id)
    if part:
        return jsonify({'success': True, 'part': part})
    return jsonify({'success': False, 'message': 'Запчасть не найдена'}), 404

# ========== API ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

@app.route('/api/user', methods=['POST'])
def create_or_get_user():
    """Создание или получение пользователя"""
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    
    if not name or not phone:
        return jsonify({'success': False, 'message': 'Имя и телефон обязательны'}), 400
    
    user = db.get_or_create_user(name, phone, email)
    
    # Сохраняем в сессию
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_phone'] = user['phone']
    session['user_email'] = user['email']
    session.permanent = True
    
    return jsonify({'success': True, 'user': user})

@app.route('/api/user', methods=['GET'])
def get_user():
    """Получение текущего пользователя"""
    user = get_current_user()
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'message': 'Пользователь не авторизован'}), 401

@app.route('/api/user/logout', methods=['POST'])
def logout():
    """Выход пользователя"""
    session.clear()
    return jsonify({'success': True, 'message': 'Выход выполнен'})

@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    """Обновление профиля пользователя"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    data = request.json
    name = data.get('name')
    email = data.get('email')
    
    if not name:
        return jsonify({'success': False, 'message': 'Имя обязательно'}), 400
    
    success = db.update_user_profile(user['id'], name, email)
    
    if success:
        # Обновляем сессию
        session['user_name'] = name
        session['user_email'] = email
        return jsonify({
            'success': True, 
            'message': 'Профиль обновлен',
            'user': {'id': user['id'], 'name': name, 'phone': user['phone'], 'email': email}
        })
    
    return jsonify({'success': False, 'message': 'Ошибка при обновлении'}), 400

# ========== API ДЛЯ РАБОТЫ С ЗАКАЗАМИ ==========

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Создание нового заказа"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    data = request.json
    items = data.get('items', [])
    total_price = data.get('total_price', 0)
    
    if not items:
        return jsonify({'success': False, 'message': 'Корзина пуста'}), 400
    
    # Проверяем наличие товаров
    for item in items:
        part = db.get_part_by_id(item['id'])
        if not part:
            return jsonify({'success': False, 'message': f'Товар {item["name"]} не найден'}), 400
    
    order_id = db.create_order(user['id'], items, total_price)
    
    return jsonify({
        'success': True, 
        'message': 'Заказ успешно создан',
        'order_id': order_id
    })

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Получение заказов текущего пользователя"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    orders = db.get_user_orders(user['id'])
    return jsonify({'success': True, 'orders': orders})

# ========== API ДЛЯ РАБОТЫ С ЗАПИСЯМИ ==========

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Создание новой записи на ТО"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    data = request.json
    
    # Валидация данных
    required_fields = ['carBrand', 'carModel', 'carYear', 'serviceType', 'date', 'time']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Поле {field} обязательно'}), 400
    
    appointment_id = db.create_appointment(user['id'], data)
    
    return jsonify({
        'success': True,
        'message': 'Запись успешно создана',
        'appointment_id': appointment_id
    })

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Получение записей текущего пользователя"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    appointments = db.get_user_appointments(user['id'])
    return jsonify({'success': True, 'appointments': appointments})

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    """Отмена записи"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    success = db.cancel_appointment(appointment_id, user['id'])
    
    if success:
        return jsonify({'success': True, 'message': 'Запись отменена'})
    return jsonify({'success': False, 'message': 'Не удалось отменить запись'}), 400

# ========== API ДЛЯ РАБОТЫ С АВТОМОБИЛЯМИ ==========

@app.route('/api/user/cars', methods=['GET'])
def get_user_cars():
    """Получение автомобилей пользователя"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    cars = db.get_user_cars(user['id'])
    return jsonify({'success': True, 'cars': cars})

@app.route('/api/user/cars', methods=['POST'])
def add_user_car():
    """Добавление автомобиля"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    data = request.json
    
    # Валидация
    required_fields = ['brand', 'model']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Поле {field} обязательно'}), 400
    
    car_id = db.add_user_car(user['id'], data)
    
    return jsonify({
        'success': True,
        'message': 'Автомобиль добавлен',
        'car_id': car_id
    })

@app.route('/api/user/cars/<int:car_id>', methods=['DELETE'])
def delete_user_car(car_id):
    """Удаление автомобиля"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Необходима авторизация'}), 401
    
    success = db.delete_user_car(car_id, user['id'])
    
    if success:
        return jsonify({'success': True, 'message': 'Автомобиль удален'})
    return jsonify({'success': False, 'message': 'Автомобиль не найден'}), 404

# ========== API ДЛЯ РАБОТЫ С ЧАТОМ ==========

@app.route('/api/chat/messages', methods=['POST'])
def send_chat_message():
    """Отправка сообщения в чат"""
    user = get_current_user()
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'success': False, 'message': 'Сообщение не может быть пустым'}), 400
    
    user_id = user['id'] if user else None
    user_name = user['name'] if user else 'Гость'
    
    # Сохраняем сообщение пользователя
    db.save_chat_message(user_id, user_name, message, is_support=False)
    
    # Генерируем автоматический ответ
    auto_response = get_auto_response(message)
    if auto_response:
        db.save_chat_message(user_id, 'Система', auto_response, is_support=True)
        return jsonify({
            'success': True,
            'message': 'Сообщение отправлено',
            'auto_response': auto_response
        })
    
    return jsonify({
        'success': True,
        'message': 'Сообщение отправлено'
    })

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Получение истории чата"""
    user = get_current_user()
    user_id = user['id'] if user else None
    
    if not user_id:
        return jsonify({'success': True, 'messages': []})
    
    # Получаем историю сообщений
    messages = db.get_chat_history(user_id)
    
    # Отмечаем сообщения как прочитанные
    if messages:
        db.mark_messages_as_read(user_id)
    
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/chat/unread', methods=['GET'])
def get_unread_count():
    """Получение количества непрочитанных сообщений"""
    user = get_current_user()
    if not user:
        return jsonify({'success': True, 'count': 0})
    
    count = db.get_unread_messages(user['id'])
    return jsonify({'success': True, 'count': count})

@app.route('/api/chat/read', methods=['POST'])
def mark_chat_read():
    """Отметить сообщения как прочитанные"""
    user = get_current_user()
    if user:
        db.mark_messages_as_read(user['id'])
    return jsonify({'success': True})

def get_auto_response(message):
    """Автоматические ответы на частые вопросы"""
    message = message.lower()
    
    # Словарь с ответами на ключевые слова
    responses = {
        'записаться': 'Вы можете записаться через форму на сайте в разделе "Запись" или по телефону +7 (999) 123-45-67',
        'запись': 'Для записи на ТО перейдите в раздел "Запись" на сайте или позвоните нам +7 (999) 123-45-67',
        'акци': 'Наши текущие акции:\n• Скидка 20% на замену масла\n• Бесплатная диагностика при комплексном ТО\n• Скидка 10% на запчасти при заказе услуг',
        'скидк': 'Действующие скидки:\n• 20% на замену масла\n• 10% на запчасти\n• Бесплатная диагностика',
        'цена': 'Стоимость услуг:\n• Замена масла - от 1500₽\n• Диагностика - от 1000₽\n• Ремонт тормозов - от 2000₽\n• Ремонт подвески - от 2500₽\n• Заправка кондиционера - от 1800₽\n• Комплексное ТО - от 5000₽',
        'стоимост': 'Цены на услуги:\n• Замена масла - от 1500₽\n• Диагностика - от 1000₽\n• ТО - от 5000₽',
        'время': 'Мы работаем:\n• Пн-Пт: 9:00 - 20:00\n• Сб: 10:00 - 18:00\n• Вс: 10:00 - 16:00',
        'график': 'Режим работы:\nПн-Пт 9:00-20:00\nСб-Вс 10:00-18:00',
        'адрес': 'Наш адрес: г. Москва, ул. Автомобильная, д. 10 (метро "Автозаводская")',
        'телефон': 'Наш телефон: +7 (999) 123-45-67\nWhatsApp/Telegram: +7 (999) 123-45-67',
        'контакт': 'Связаться с нами:\n• Телефон: +7 (999) 123-45-67\n• Email: info@autoservice.ru\n• Адрес: ул. Автомобильная, д. 10',
        'спасибо': 'Пожалуйста! Обращайтесь еще 😊 Рады помочь!',
        'пасиб': 'Всегда пожалуйста! 😊',
        'благодар': 'Спасибо за добрые слова! Будем рады видеть вас снова!',
        'привет': 'Здравствуйте! Чем могу помочь?',
        'здравствуй': 'Добрый день! Чем я могу вам помочь?',
        'добрый': 'Здравствуйте! Какой у вас вопрос?',
        'работа': 'Режим работы:\nПн-Пт: 9:00 - 20:00\nСб-Вс: 10:00 - 18:00',
        'масло': 'Замена масла от 1500₽. Используем масла ведущих производителей: Mobil, Shell, Castrol. Работа занимает около 1 часа.',
        'диагностик': 'Компьютерная диагностика от 1000₽. Проверка всех систем автомобиля, выявление ошибок, рекомендации по ремонту.',
        'тормоз': 'Ремонт тормозной системы от 2000₽:\n• Замена колодок\n• Замена дисков\n• Прокачка тормозов\n• Замена жидкости',
        'подвеск': 'Ремонт подвески от 2500₽:\n• Замена амортизаторов\n• Замена шаровых опор\n• Замена сайлентблоков\n• Сход-развал',
        'кондиционер': 'Заправка кондиционера от 1800₽. Включает диагностику системы, проверку на утечки, заправку фреоном.',
        'то': 'Комплексное ТО от 5000₽:\n• Замена масла и фильтров\n• Проверка всех систем\n• Диагностика\n• Рекомендации',
        'запчасти': 'В нашем каталоге более 5000 запчастей в наличии. Оригинальные и качественные аналоги. Доставка по Москбесплатно при заказе от 3000₽.',
        'доставка': 'Доставка запчастей:\n• По Москве - бесплатно от 3000₽\n• Доставка курьером - 300₽\n• Самовывоз из магазина',
        'гарантия': 'На все работы гарантия 1 год. На запчасти - гарантия производителя (от 6 месяцев до 2 лет).',
        'оплат': 'Способы оплаты:\n• Наличные\n• Банковская карта\n• Перевод на карту\n• Безналичный расчет для юрлиц',
        'выходн': 'Мы работаем без выходных! В субботу и воскресенье с 10:00 до 18:00'
    }
    
    # Ищем ключевые слова в сообщении
    for key, response in responses.items():
        if key in message:
            return response
    
    # Если ничего не найдено, возвращаем None (оператор ответит позже)
    return None

# ========== API ДЛЯ СТАТИСТИКИ ==========

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получение статистики"""
    stats = {
        'clients': '2,500+',
        'works': '3,200+',
        'parts': '5,000+',
        'support': '24/7'
    }
    return jsonify({'success': True, 'stats': stats})

# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    