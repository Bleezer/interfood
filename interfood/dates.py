"""A gyűjtési időszak dátumszámítása."""

from datetime import timedelta


def next_monday(today):
    return today + timedelta(days=7 - today.weekday())
