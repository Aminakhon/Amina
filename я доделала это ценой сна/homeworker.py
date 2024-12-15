from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import jwt
import time
from functools import wraps

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cd_collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)



class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    country = db.Column(db.String(4))
    phone = db.Column(db.String(100), nullable=False, unique=True)
    isPublic = db.Column(db.Boolean)
    image = db.Column(db.String(100))
    last_generation = db.Column(db.Integer, nullable=True)




def present_person(user):
    return {
        'id': user.id,
        'email': user.email,
        'login': user.login,
        'name': user.name,
        'description': user.description,
        'country': user.country,
        'phone': user.phone,
        'isPublic': user.isPublic,
        'image': user.image
    }


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alpha2 = db.Column(db.String(3), nullable=False)
    alpha3 = db.Column(db.String(4), nullable=False)
    region = db.Column(db.String(100))



def present_country(country):
    return {
        'id': country.id,
        'name': country.name,
        'alpha2': country.alpha2,
        'alpha3': country.alpha3,
        'region': country.region
    }

def requires_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # получаем токен из заголовков запроса
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        # если токена нет - возвращаем ошибку
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        # расшифровываем токен и получаем его содержимое
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401

        # получаем id пользователя и время генерации из токена
        user_id = payload.get('user_id')
        created_at = payload.get('created_at')

        # если чего-то нет - возвращаем ошибку
        if not user_id or not created_at:
            return jsonify({'error': 'Invalid token'}), 401

        # находим пользователя, если его нет - возвращаем ошибку
        user = Person.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 401

        # если с момента генерации прошло больше суток, просим войти заного
        if created_at + 60 * 60 * 24 < int(time.time()):
            return jsonify({'error': 'Token expired'}), 401

        # передаем в целевой эндпоинт пользователя и параметры пути
        return func(user, *args, **kwargs)

    return wrapper


@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    # забираем всех исполнителей из базы
    countries = Country.query.all()
    # превращаем их в список словарей
    countries_descriptions = [present_country(country) for country in countries]
    # возвращаем ответ в виде списка словарей и типом application/json
    return jsonify(countries_descriptions)


@app.route('/api/country/<string:alpha>', methods=['GET'])
def get_artist_by_id(alpha):
    alpha2 = Country.query.filter_by(alpha2=alpha).first()
    if not alpha2:
        return jsonify({'reason': 'Alpha2 not found'}), 404
    return jsonify(present_country(alpha2)), 200


@app.route('/api/registration', methods=['POST'])
def add_person():
    # получаем данные, отправленные пользователем в формате словаря
    data = request.get_json()
    if data is None:
        return jsonify({'reason': 'Invalid JSON format'}), 400
    login = data.get('login')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    description = data.get('description')
    country = data.get('country')
    phone = data.get('phone')
    isPublic = data.get('isPublic')
    image = data.get('image')

    if not login:
        return jsonify({'reason': 'Missing login'}), 400

    if not email:
        return jsonify({'reason': 'Missing email'}), 400

    if not phone:
        return jsonify({'reason': 'Missing phone'}), 400

    if not password:
        return jsonify({'reason': 'Missing password'}), 400

    if isPublic != True and isPublic != False:
        return jsonify({'reason': 'Missing isPublic'}), 400

    if Person.query.filter_by(name=name).first():
        return jsonify({'reason': 'Person already exists'}), 400
    if Person.query.filter_by(login=login).first():
        return jsonify({'reason': 'Person already exists'}), 400
    if Person.query.filter_by(email=email).first():
        return jsonify({'reason': 'Person already exists'}), 400
    if Person.query.filter_by(phone=phone).first():
        return jsonify({'reason': 'Person already exists'}), 400
    if not Country.query.filter_by(alpha2=country).first():
        return jsonify({'reason': 'Country not exists'}), 400
    password2 = bcrypt.generate_password_hash(password)
    print(password2)
    user = Person(login=login, name=name, email=email, password=password2, description=description, country=country,
                  phone=phone, isPublic=isPublic, image=image)

    db.session.add(user)
    db.session.commit()
    return jsonify(present_person(user))

@app.route('/api/delete/<int:id>', methods=['DELETE'])
def delete_person(id):
    # находим артиста в базе и возвращаем ошибку, если его нет
    user = Person.query.filter_by(id=id).first()

    if not user:
        return jsonify({'reason':'User not found'}), 400
    # удаляем запись
    db.session.delete(user)
    # сохраняем изменения
    db.session.commit()

    # возвращаем успешный ответ
    return jsonify({'success': True})

@app.route('/api/sign_in', methods=['POST'])
def login():
    data = request.get_json()

    login = data.get('login')
    password = data.get('password')

    if not login or not password:
        return jsonify({'error': 'Missing data'}), 400

    # ищем пользователя в базе и проверяем хэш пароля
    user = Person.query.filter_by(login=login).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # генерируем токен с id пользователя и временем создания
    token = jwt.encode({'user_id': user.id, 'created_at': int(time.time())}, app.config['SECRET_KEY'],
                       algorithm='HS256')

    return jsonify({'token': token}), 200

@app.route('/api/me/profile', methods=['GET'])
@requires_user
def generate_number(user):
    # если пользователь посылает запросы чаще раза в секунду - отправляем ошибку
    if user.last_generation == int(time.time()):
        return jsonify({'error': 'Too many request per second'}), 401

    user.last_generation = int(time.time())
    db.session.commit()

    return jsonify(present_person(user)), 200


@app.route('/api/me/profile', methods=['PATCH'])
@requires_user
def update_artist(user):
    data = request.get_json()
    if user.last_generation == int(time.time()):
        return jsonify({'error': 'Too many request per second'}), 401
    if 'name' in data:
        name = data.get('name')

        if not name:
            return jsonify({'reason': 'Missing name'}), 400

        if name != user.name and Person.query.filter_by(name=name).first():
            return jsonify({'reason': 'Person already exists'}), 400

        user.name = name

    if 'login' in data:
        login = data.get('login')

        if not login:
            return jsonify({'reason': 'Missing login'}), 400

        if login != user.login and Person.query.filter_by(login=login).first():
            return jsonify({'reason': 'Person already exists'}), 400

        user.login = login

    if 'email' in data:
        email = data.get('email')

        if not email:
            return jsonify({'reason': 'Missing email'}), 400

        if email != user.email and Person.query.filter_by(email=email).first():
            return jsonify({'reason': 'Person already exists'}), 400

        user.email = email

    if 'description' in data:
        description = data.get('description')

        user.description = description

    if 'country' in data:
        country = data.get('country')

        if not country:
            return jsonify({'reason': 'Missing country'}), 400
        if not Country.query.filter_by(alpha2=country).first():
            return jsonify({'reason': 'No in list'}), 400
        user.country = country

    if 'phone' in data:
        phone = data.get('phone')

        if not phone:
            return jsonify({'reason': 'Missing phone'}), 400

        if phone != user.phone and Person.query.filter_by(phone=phone).first():
            return jsonify({'reason': 'Person already exists'}), 400

        user.phone = phone

    if 'isPublic' in data:
        isPublic = data.get('isPublic')

        if not isPublic:
            return jsonify({'reason': 'Missing isPublic'}), 400

        if isPublic != False and isPublic!=True:
            return jsonify({'reason': 'Not right variant'}), 400

        user.isPublic = isPublic

    if 'image' in data:
        image = data.get('image')

        user.image = image
    user.last_generation = int(time.time())
    db.session.commit()
    return jsonify(present_person(user)), 200

@app.route('/api/profiles/<string:login>', methods=['GET'])
@requires_user
def look_at(user, login):
    if not login:
        return jsonify({'error': 'Missing profile'}), 400
    if user.last_generation == int(time.time()):
        return jsonify({'error': 'Too many request per second'}), 401
    if not Person.query.filter_by(login=login).first():
        return jsonify({'error': 'Wrong login'}), 400
    friend = Person.query.filter_by(login=login).first()
    if not friend.isPublic and not friend == user:
        return jsonify({'error': 'Closed profile'}), 400
    user.last_generation = int(time.time())
    db.session.commit()
    return jsonify(present_person(friend)), 200


@app.route('/api/me/updatePassword', methods=['POST'])
@requires_user
def update_password(user):
    data = request.get_json()
    if not bcrypt.check_password_hash(user.password, data.get('old_password')):
        return jsonify({'error': 'Wrong password'}), 400
    password2 = bcrypt.generate_password_hash(data.get('new_password'))
    user.password = password2
    token = jwt.encode({'user_id': user.id, 'created_at': int(time.time())}, app.config['SECRET_KEY'],
                       algorithm='HS256')
    print(token)
    db.session.commit()
    return jsonify({'token':token}), 200
if __name__ == '__main__':
    # запускаем сервер
    app.run()
