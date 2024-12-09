class NotEnoughBalanceException(Exception):
    def __init__(self, price: int, balance: int):
        self.message = f"Not enough balance to buy this property. Price: {price}, Balance: {balance}"
        super().__init__(self.message)
