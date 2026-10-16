"""One retained shipping function plus independently authored run compression."""


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


def compress_runs(symbols):
    encoded = []
    iterator = iter(symbols)
    marker = object()
    previous = next(iterator, marker)
    length = 1
    for symbol in iterator:
        if symbol == previous:
            length += 1
            continue
        encoded.append((previous, length))
        previous = symbol
        length = 1
    if previous is not marker:
        encoded.append((previous, length))
    return tuple(encoded)
