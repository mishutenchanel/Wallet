import os
import uuid
import logging
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import UUID
from flask_migrate import Migrate
from waitress import serve
import redis
from redis.lock import Lock

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///wallets.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 50,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Подключение к Redis
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=os.getenv('REDIS_PORT', 6379), db=0)


class Wallet(db.Model):
    __tablename__ = 'wallets'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = db.Column(db.Float, nullable=False, default=0.0)


# Инициализация базы данных
with app.app_context():
    db.create_all()


# Пополнение / снятие средств
@app.route('/api/v1/wallets/<uuid:wallet_uuid>/operation', methods=['POST'])
def wallet_operation(wallet_uuid):
    data = request.get_json()
    if not data or 'operationType' not in data or 'amount' not in data:
        return jsonify({"error": "Invalid request data"}), 400

    operation_type = data['operationType'].upper()
    amount = data['amount']

    if operation_type not in ['DEPOSIT', 'WITHDRAW'] or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Invalid operation type or amount"}), 400

    # Использование Redis для блокировки
    lock = Lock(redis_client, f"wallet_lock_{wallet_uuid}", timeout=10, blocking_timeout=5)
    try:
        with lock:
            wallet = db.session.execute(
                db.select(Wallet).where(Wallet.uuid == wallet_uuid).with_for_update()
            ).scalar_one_or_none()

            if not wallet:
                return jsonify({"error": "Wallet not found"}), 404

            if operation_type == 'DEPOSIT':
                wallet.balance += amount
            elif operation_type == 'WITHDRAW':
                if wallet.balance < amount:
                    return jsonify({"error": "Insufficient funds"}), 400
                wallet.balance -= amount

            db.session.commit()
            redis_client.set(f"wallet_balance_{wallet_uuid}", wallet.balance)
            return jsonify({"message": "Operation successful", "balance": wallet.balance}), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error during wallet operation: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# Получение баланса кошелька
@app.route('/api/v1/wallets/<uuid:wallet_uuid>', methods=['GET'])
def get_balance(wallet_uuid):
    # Попытка получить баланс из кеша Redis
    cached_balance = redis_client.get(f"wallet_balance_{wallet_uuid}")
    if cached_balance:
        return jsonify({"balance": float(cached_balance)}), 200

    wallet = db.session.execute(db.select(Wallet).where(Wallet.uuid == wallet_uuid)).scalar_one_or_none()

    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    redis_client.set(f"wallet_balance_{wallet_uuid}", wallet.balance)
    return jsonify({"balance": wallet.balance}), 200


# Создание кошелька
@app.route('/api/v1/wallets', methods=['POST'])
def create_wallet():
    new_wallet = Wallet()
    db.session.add(new_wallet)
    db.session.commit()
    return jsonify({"message": "Wallet created", "wallet_id": new_wallet.uuid, "balance": new_wallet.balance}), 201

# Просмотр всех кошельков
@app.route('/api/v1/wallets', methods=['GET'])
def get_all_wallets():
    wallets = Wallet.query.all()
    wallet_list = [{"uuid": str(wallet.uuid), "balance": wallet.balance} for wallet in
                   wallets]
    return jsonify(wallet_list), 200


@app.route('/')
def home():
    return render_template('index.html')


# Запуск приложения
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
