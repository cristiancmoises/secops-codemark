"""Independently authored order summary; no source block is copied."""

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP


def describe_basket(records, catalog):
    counts = Counter()
    for record in records:
        product, count = record
        if product in catalog and isinstance(count, int) and count > 0:
            counts.update({product: count})
    lines = []
    amounts = []
    for product, count in counts.most_common():
        price = Decimal(str(catalog[product]))
        amount = (price * Decimal(count)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        amounts.append(amount)
        lines.append("{} x {} = {}".format(count, product, amount))
    return {"lines": tuple(lines), "amount": sum(amounts, Decimal(0))}


def pack_by_capacity(records, capacity):
    if capacity < 1:
        raise ValueError("positive capacity required")
    packages = []
    current = []
    for product, count in records:
        for _ in range(max(0, count)):
            current.append(product)
            if len(current) == capacity:
                packages.append(tuple(current))
                current.clear()
    if current:
        packages.append(tuple(current))
    return tuple(packages)
