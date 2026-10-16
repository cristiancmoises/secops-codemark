"""Independently authored maze solver, unrelated to the order ledger."""

from collections import deque


def shortest_route(board, origin, destination):
    height = len(board)
    width = len(board[0]) if height else 0
    queue = deque([(origin, ())])
    visited = {origin}
    while queue:
        location, route = queue.popleft()
        route = (*route, location)
        if location == destination:
            return route
        row, column = location
        for next_row, next_column in (
            (row + 1, column),
            (row - 1, column),
            (row, column + 1),
            (row, column - 1),
        ):
            neighbor = next_row, next_column
            inside = 0 <= next_row < height and 0 <= next_column < width
            if inside and board[next_row][next_column] != "#" and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, route))
    return ()
