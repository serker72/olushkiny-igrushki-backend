from decimal import Decimal


def get_percent(
    current: int | float | Decimal | None, general: int | float | Decimal | None, accuracy: int = 2
) -> Decimal | int:
    """Расчет процента"""
    if current is not None and general is not None:
        return Decimal(round((current / general) * 100, accuracy))
    return 0
