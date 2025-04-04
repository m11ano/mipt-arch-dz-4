from converters import CurrencyConverter, ExchangeRateService

TICKER = 'RUB'

class UsdRubConverter(CurrencyConverter):
    def __init__(self):
        self.rate_service = ExchangeRateService()

    async def convert(self, amount: float) -> float:
        rates = await self.rate_service.get_rates()
        if not rates or TICKER not in rates:
            return 0.0
        return amount * rates[TICKER]
    