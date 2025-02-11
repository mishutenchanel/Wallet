from locust import HttpUser, task, between
import uuid

class WalletUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(0.1, 0.5)

    def on_start(self):
        # Создание нового кошелька перед началом теста
        response = self.client.post("/api/v1/wallets")
        if response.status_code == 201:
            wallet_data = response.json()
            self.wallet_uuid = wallet_data["wallet_id"]
        else:
            print("Ошибка при создании кошелька.")
            self.wallet_uuid = None

    @task(2)
    def deposit_money(self):
        if self.wallet_uuid:
            self.client.post(
                f"/api/v1/wallets/{self.wallet_uuid}/operation",
                json={"operationType": "DEPOSIT", "amount": 10}
            )
        else:
            print("Ошибка: кошелек не создан.")

    @task(1)
    def withdraw_money(self):
        if self.wallet_uuid:
            self.client.post(
                f"/api/v1/wallets/{self.wallet_uuid}/operation",
                json={"operationType": "WITHDRAW", "amount": 10}
            )
        else:
            print("Ошибка: кошелек не создан.")

    @task(3)
    def get_balance(self):
        if self.wallet_uuid:
            self.client.get(f"/api/v1/wallets/{self.wallet_uuid}")
        else:
            print("Ошибка: кошелек не создан.")
