"""Synthetic order ledger for the reproducible similarity fixture."""


def render_ledger(buckets, allocation):
    rows = []
    grand_total = 0
    for name in sorted(buckets):
        entry = buckets[name]
        amount = entry["cents"] + allocation.get(name, 0)
        grand_total += amount
        rows.append(f"{name}: {entry['units']} units, {amount // 100}.{amount % 100:02d}")
    rows.append(f"TOTAL {grand_total // 100}.{grand_total % 100:02d}")
    return "\n".join(rows)


def accumulate_orders(orders, unit_prices):
    buckets = {}
    rejected = []
    for position, order in enumerate(orders):
        item = order.get("item", "")
        quantity = order.get("quantity", 0)
        if item not in unit_prices or quantity <= 0:
            rejected.append(position)
            continue
        subtotal = quantity * unit_prices[item]
        if quantity >= 12:
            subtotal = subtotal * 9 // 10
        entry = buckets.setdefault(item, {"units": 0, "cents": 0})
        entry["units"] += quantity
        entry["cents"] += subtotal
    return buckets, rejected


def allocate_shipping(buckets, shipping_cents):
    total_units = sum(entry["units"] for entry in buckets.values())
    allocation = {}
    remaining = shipping_cents
    names = sorted(buckets)
    for index, name in enumerate(names):
        if index == len(names) - 1:
            share = remaining
        elif total_units:
            share = shipping_cents * buckets[name]["units"] // total_units
        else:
            share = 0
        allocation[name] = share
        remaining -= share
    return allocation
