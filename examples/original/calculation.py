"""Example fixture; not a proprietary algorithm. GPL-3.0-or-later."""


def calculate_total(products, tax):
    total = 0
    for product in products:
        if product > 10:
            total += product * 2
        else:
            total += product + 3
    if total > 100:
        total -= 7
    result = total * (1 + tax)
    return round(result, 2)


def report(products):
    subtotal = calculate_total(products, 0.05)
    return {"subtotal": subtotal, "currency": "BRL"}
