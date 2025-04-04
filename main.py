import asyncio
from converters import (
    UsdRubConverter,
    UsdEurConverter,
    UsdGbpConverter,
    UsdCnyConverter
)

# Создадим фабрику конвертеров
def converter_factory(ticker: str):
    match ticker.upper():
        case 'RUB':
            return UsdRubConverter()
        case 'EUR':
            return UsdEurConverter()
        case 'GBP':
            return UsdGbpConverter()
        case 'CNY':
            return UsdCnyConverter()
        case _:
            raise ValueError(f"Неизвестный тикер валюты: {ticker}")

async def main():

    # Добавим обработку ошибок на случай ввода не числа
    amount_str = input('Введите сумму в USD: \n')
    try:
        amount = float(amount_str)
    except ValueError:
        print("Ошибка ввода. Введите число.")
        return

    currency_list = ['RUB', 'EUR', 'GBP', 'CNY']

    tasks = []
    for cur in currency_list:
        converter = converter_factory(cur)
        tasks.append(asyncio.create_task(converter.convert(amount)))

    results = await asyncio.gather(*tasks)

    # Выводим результаты
    for cur, res in zip(currency_list, results):
        print(f"{amount} USD to {cur}: {res:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
