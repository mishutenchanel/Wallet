from locust import HttpUser, task, between


class WalletUser(HttpUser):
    host = "http://localhost:5000"
    wait_time = between(0.1, 0.5)

    def __init__(self, environment):
        super().__init__(environment)
        self.wallet_uuid = "4a0df525-0e51-4b81-be4f-ecd765fadb70"

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
