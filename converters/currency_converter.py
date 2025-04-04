from abc import ABC, abstractmethod

"""
Абстрактный класс теперь содержит всего один асинхронный метод: async convert(amount).
Тем самым устраняем нарушение принципа разделения интерфейсов.
"""

class CurrencyConverter(ABC):
    @abstractmethod
    async def convert(self, amount: float) -> float:
        pass