"""Synthetic order ledger for the reproducible similarity fixture."""


def collect_lines(records, price_table):
    groups = {}
    invalid_positions = []
    for row_number, record in enumerate(records):
        product = record.get("item", "")
        count = record.get("quantity", 0)
        if product not in price_table or count <= 0:
            invalid_positions.append(row_number)
            continue
        line_cents = count * price_table[product]
        if count >= 12:
            line_cents = line_cents * 9 // 10
        group = groups.setdefault(product, {"units": 0, "cents": 0})
        group["units"] += count
        group["cents"] += line_cents
    return groups, invalid_positions


def spread_postage(groups, postage):
    unit_count = sum(group["units"] for group in groups.values())
    charges = {}
    unassigned = postage
    products = sorted(groups)
    for offset, product_name in enumerate(products):
        if offset == len(products) - 1:
            portion = unassigned
        elif unit_count:
            portion = postage * groups[product_name]["units"] // unit_count
        else:
            portion = 0
        charges[product_name] = portion
        unassigned -= portion
    return charges


def format_statement(groups, charges):
    lines = []
    combined = 0
    for product_name in sorted(groups):
        group = groups[product_name]
        line_total = group["cents"] + charges.get(product_name, 0)
        combined += line_total
        lines.append(f"{product_name}: {group['units']} units, {line_total // 100}.{line_total % 100:02d}")
    lines.append(f"TOTAL {combined // 100}.{combined % 100:02d}")
    return "\n".join(lines)
