from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import re
from datetime import datetime, date
import os

hotel_details = {
    "title": "ЗооТель",
    "location": "Санкт-Петербург",
    "tagline": "Комфорт для вашего питомца!",
    "address": "пр. Ленина, д. 10",
    "contact": "+7(812)987-65-43",
    "email": "booking@zootel.ru",
}

available_rooms = [
    {"number": 101, "category": "Эконом", "rate": 450, "species": "кошка", "dimensions": "маленький"},
    {"number": 102, "category": "Стандарт", "rate": 750, "species": "кошка", "dimensions": "средний"},
    {"number": 201, "category": "Комфорт", "rate": 1100, "species": "собака", "dimensions": "средний"},
    {"number": 202, "category": "Люкс", "rate": 1800, "species": "собака", "dimensions": "большой"},
    {"number": 103, "category": "Мини", "rate": 380, "species": "кошка", "dimensions": "маленький"},
    {"number": 301, "category": "Семейный", "rate": 2400, "species": "собака", "dimensions": "большой"},
]

reservations = []
feedback = ["Отличное обслуживание!", "Питомец доволен", "Чистые номера", "Удобное расположение", "Профессиональный персонал"]
is_admin_authenticated = False

def check_email(email):
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)

def check_phone(phone):
    return re.match(r'^\+7$[0-9]{3}$[0-9]{3}-[0-9]{2}-[0-9]{2}$', phone)

def validate_period(arrival, departure):
    try:
        start = datetime.strptime(arrival, "%d:%m:%Y").date()
        end = datetime.strptime(departure, "%d:%m:%Y").date()
        return start >= date.today() and end > start
    except ValueError:
        return False
def generate_homepage():
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>{hotel_details['title']}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>{hotel_details['title']}</h1>
            <p>г. {hotel_details['location']}, {hotel_details['address']}</p>
            <p>{hotel_details['tagline']}</p>
        </header>
        <section class="rooms">
            <h2>Наши номера</h2>
            <ul>
                {''.join(f"<li>{r['category']} - {r['rate']} руб./сутки</li>" for r in available_rooms[:3])}
            </ul>
        </section>
        <section class="reviews">
            <h2>Отзывы</h2>
            <ul>
                {''.join(f"<li>{rev}</li>" for rev in feedback[:3])}
            </ul>
        </section>
        <p><a href="/catalog">Смотреть все номера →</a></p>
    </body>
    </html>
    """
def render_catalog(params=None):
    if params is None:
        params = {}
    filtered = available_rooms.copy()
    
    if "species" in params and params["species"]:
        filtered = [r for r in filtered if r["species"] == params["species"]]
    
    if "sort_price" in params:
        reverse_order = params["sort_price"] == "desc"
        filtered.sort(key=lambda x: x["rate"], reverse=reverse_order)
    
    cat_selected = 'selected' if params.get("species") == "кошка" else ""
    dog_selected = 'selected' if params.get("species") == "собака" else ""
    low_to_high = 'selected' if params.get("sort_price") == "asc" else ""
    high_to_low = 'selected' if params.get("sort_price") == "desc" else ""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Каталог номеров</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>Выберите номер</h1>
        </header>
        <form action="/catalog" method="get">
            Тип животного: 
            <select name="species">
                <option value="">Все</option>
                <option value="кошка" {cat_selected}>Кошки</option>
                <option value="собака" {dog_selected}>Собаки</option>
            </select>
            Стоимость: 
            <select name="sort_price">
                <option value="" selected>По умолчанию</option>
                <option value="asc" {low_to_high}>От низкой к высокой</option>
                <option value="desc" {high_to_low}>От высокой к низкой</option>
            </select>
            <input type="submit" value="Применить">
            <button type="button" onclick="location.href='/catalog'">Очистить</button>
        </form>
        <ul>
    """
    for room in filtered:
        html += f"""
        <li>
            {room['category']} ({room['species']}) - {room['rate']} руб.
            <button onclick="location.href='/booking?room_id={room['number']}'">Забронировать</button>
        </li>
        """
    html += "</ul><p><a href='/'>← На главную</a></p></body></html>"
    return html

def show_booking_form(room_id=None):
    room = next((r for r in available_rooms if r["number"] == room_id), None)
    room_title = room["category"] if room else "Не найден"
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Бронирование: {room_title}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>Форма бронирования: {room_title}</h1>
        </header>
        <form method="post" action="/booking">
            <input type="hidden" name="room_id" value="{room_id}">
            Ваше имя: <input type="text" name="guest" required><br>
            Имя питомца: <input type="text" name="pet" required><br>
            Телефон: <input type="text" name="phone" placeholder="+7(XXX)XXX-XX-XX" required><br>
            Email: <input type="email" name="email" required><br>
            Дата заезда: <input type="text" name="arrival" placeholder="дд:мм:гггг" required><br>
            Дата выезда: <input type="text" name="departure" placeholder="дд:мм:гггг" required><br>
            <input type="submit" value="Отправить запрос">
        </form>
        <p><a href="/catalog">← К выбору номеров</a></p>
    </body>
    </html>
    """

def show_confirmation():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Спасибо!</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>Заявка отправлена!</h1>
        </header>
        <p>Наши менеджеры свяжутся с вами в ближайшее время.</p>
        <p><a href="/">← На главную</a></p>
    </body>
    </html>
    """
def show_login_error():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Ошибка</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>Неверные учетные данные</h1>
        </header>
        <p>Пожалуйста, попробуйте снова.</p>
        <p><a href="/admin">Вернуться к входу</a></p>
    </body>
    </html>
    """

def show_admin_login():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Вход</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header>
            <h1>Панель администрирования</h1>
        </header>
        <form method="post" action="/admin/login">
            Логин: <input type="text" name="login" required><br>
            Пароль: <input type="password" name="password" required><br>
            <input type="submit" value="Войти">
        </form>
    </body>
    </html>
    """

def generate_dashboard():
    table = """
    <h1>Бронирования</h1>
    <table>
        <tr><th>Гость</th><th>Питомец</th><th>Телефон</th><th>Email</th><th>Заезд</th><th>Выезд</th></tr>
    """
    for booking in reservations:
        table += f"""
        <tr>
            <td>{booking['guest']}</td>
            <td>{booking['pet']}</td>
            <td>{booking['phone']}</td>
            <td>{booking['email']}</td>
            <td>{booking['arrival']}</td>
            <td>{booking['departure']}</td>
        </tr>
        """
    table += "</table><p><a href='/'>← На главную</a></p>"
    
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Панель управления</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>{table}</body>
    </html>
    """
class HotelRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/static/"):
            try:
                file_path = self.path[1:]
                if os.path.exists(file_path):
                    self.send_response(200)
                    self.send_header("Content-type", "text/css")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404, "Файл не найден")
            except Exception as e:
                self.send_error(500, str(e))
            return
            
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        if self.path == "/":
            self.wfile.write(generate_homepage().encode("utf-8"))
        elif self.path.startswith("/catalog"):
            parsed = urlparse(self.path)
            query_params = parse_qs(parsed.query)
            self.wfile.write(render_catalog(query_params).encode("utf-8"))
        elif self.path.startswith("/booking"):
            query = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            room_id = int(query.get("room_id", [0])[0])
            self.wfile.write(show_booking_form(room_id).encode("utf-8"))
        elif self.path == "/admin":
            self.wfile.write(show_admin_login().encode("utf-8"))
        elif self.path == "/admin/panel":
            global is_admin_authenticated
            if is_admin_authenticated:
                self.wfile.write(generate_dashboard().encode("utf-8"))
            else:
                self.send_response(302)
                self.send_header("Location", "/admin")
                self.end_headers()
        else:
            self.wfile.write(b"<h1>404 Страница не найдена</h1>")
def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        form_data = parse_qs(self.rfile.read(content_length).decode())
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        if self.path == "/booking":
            guest = form_data.get("guest", [""])[0]
            pet = form_data.get("pet", [""])[0]
            phone = form_data.get("phone", [""])[0]
            email = form_data.get("email", [""])[0]
            arrival = form_data.get("arrival", [""])[0]
            departure = form_data.get("departure", [""])[0]
            room_id = int(form_data.get("room_id", [0])[0])
            
            validation_errors = []
            
            if not all(c.isalpha() or c in [' ', '.', '-'] for c in guest.strip()):
                validation_errors.append("Имя гостя должно содержать только буквы, пробелы, точки и тире")
            if not all(c.isalpha() or c in [' ', '-'] for c in pet.strip()):
                validation_errors.append("Имя питомца должно содержать только буквы, пробелы и дефисы")
            if not check_email(email):
                validation_errors.append("Некорректный email")
            if not check_phone(phone):
                validation_errors.append("Некорректный телефон")
            if not validate_period(arrival, departure):
                validation_errors.append("Некорректные даты")
            if not any(r["number"] == room_id for r in available_rooms):
                validation_errors.append("Неверный номер комнаты")
            for booking in reservations:
                if booking.get("room_id") == room_id:
                    existing_arrival = datetime.strptime(booking["arrival"], "%d:%m:%Y").date()
                    existing_departure = datetime.strptime(booking["departure"], "%d:%m:%Y").date()
                    new_arrival = datetime.strptime(arrival, "%d:%m:%Y").date()
                    new_departure = datetime.strptime(departure, "%d:%m:%Y").date()
                    
                    if not (new_departure <= existing_arrival or new_arrival >= existing_departure):
                        validation_errors.append("Выбранные даты пересекаются с существующим бронированием")
            
            if validation_errors:
                error_page = """
                <!DOCTYPE html>
                <html lang="ru">
                <head><meta charset="UTF-8"><title>Ошибка</title><link rel="stylesheet" href="/static/style.css"></head>
                <body>
                    <h2>Ошибка валидации:</h2>
                    <ul>
                """ + ''.join(f'<li>{e}</li>' for e in validation_errors) + """
                    </ul>
                    <a href="javascript:history.back()">Назад</a>
                </body>
                </html>
                """
                self.wfile.write(error_page.encode("utf-8"))
            else:
                reservations.append({
                    "room_id": room_id,
                    "guest": guest,
                    "pet": pet,
                    "phone": phone,
                    "email": email,
                    "arrival": arrival,
                    "departure": departure,
                })
                self.wfile.write(show_confirmation().encode("utf-8"))
                
        elif self.path == "/admin/login":
            login = form_data.get("login", [""])[0]
            password = form_data.get("password", [""])[0]
            
            if login == "admin" and password == "PROF2023":
                global is_admin_authenticated
                is_admin_authenticated = True
                self.send_response(302)
                self.send_header("Location", "/admin/panel")
                self.end_headers()
            else:
                self.wfile.write(show_login_error().encode("utf-8"))
def start_server():
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, HotelRequestHandler)
    print("Сервер запущен на порту 8000...")
    httpd.serve_forever()

if name == "main":
    start_server()