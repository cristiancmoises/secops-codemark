"""Controlled copy for comparison tests. GPL-3.0-or-later."""


def compute_total(items, rate):
    sum_value = 0
    for entry in items:
        if entry > 10:
            sum_value += entry * 2
        else:
            sum_value += entry + 3
    if sum_value > 100:
        sum_value -= 7
    output = sum_value * (1 + rate)
    return round(output, 2)


def overview(items):
    base = compute_total(items, 0.05)
    return {"subtotal": base, "currency": "BRL"}
