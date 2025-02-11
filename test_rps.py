from locust import HttpUser, task, between


class WalletUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(1, 3)

    wallet_uuid = "xxxxx"  # Замените на реальный UUID кошелька

    @task(2)
    def deposit_money(self):
        if self.wallet_uuid:
            self.client.post(
                f"/api/v1/wallets/{self.wallet_uuid}/operation",
                json={"operationType": "DEPOSIT", "amount": 10}
            )
        else:
            print("Ошибка: кошелек не задан.")

    @task(1)
    def withdraw_money(self):
        if self.wallet_uuid:
            self.client.post(
                f"/api/v1/wallets/{self.wallet_uuid}/operation",
                json={"operationType": "WITHDRAW", "amount": 10}
            )
        else:
            print("Ошибка: кошелек не задан.")

    @task(3)
    def get_balance(self):
        if self.wallet_uuid:
            self.client.get(f"/api/v1/wallets/{self.wallet_uuid}")
        else:
            print("Ошибка: кошелек не задан.")