import pytest
from app import app, db, Wallet


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


# Тест создания кошелька
def test_create_wallet(client):
    response = client.post('/api/v1/wallets')
    data = response.get_json()
    assert response.status_code == 201
    assert 'wallet_id' in data
    assert data['balance'] == 0.0


# Тест получения баланса кошелька
def test_get_balance(client):
    create_response = client.post('/api/v1/wallets')
    wallet_id = create_response.get_json()['wallet_id']

    response = client.get(f'/api/v1/wallets/{wallet_id}')
    data = response.get_json()

    assert response.status_code == 200
    assert data['balance'] == 0.0


# Тест пополнения баланса
def test_deposit_money(client):
    create_response = client.post('/api/v1/wallets')
    wallet_id = create_response.get_json()['wallet_id']

    response = client.post(f'/api/v1/wallets/{wallet_id}/operation',
                           json={"operationType": "DEPOSIT", "amount": 50})
    data = response.get_json()

    assert response.status_code == 200
    assert data['balance'] == 50.0


# Тест снятия денег
def test_withdraw_money(client):
    create_response = client.post('/api/v1/wallets')
    wallet_id = create_response.get_json()['wallet_id']

    client.post(f'/api/v1/wallets/{wallet_id}/operation',
                json={"operationType": "DEPOSIT", "amount": 100})

    response = client.post(f'/api/v1/wallets/{wallet_id}/operation',
                           json={"operationType": "WITHDRAW", "amount": 40})
    data = response.get_json()

    assert response.status_code == 200
    assert data['balance'] == 60.0


# Тест недостатка средств
def test_insufficient_funds(client):
    create_response = client.post('/api/v1/wallets')
    wallet_id = create_response.get_json()['wallet_id']

    response = client.post(f'/api/v1/wallets/{wallet_id}/operation',
                           json={"operationType": "WITHDRAW", "amount": 100})
    data = response.get_json()

    assert response.status_code == 400
    assert data['error'] == "Insufficient funds"
