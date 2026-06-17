from canvas_reminder.canvas_client import parse_next_link


def test_parse_next_link_returns_next_url():
    header = '<https://canvas.example/api/v1/users/self/todo?page=2>; rel="next", <https://canvas.example/api/v1/users/self/todo?page=3>; rel="last"'

    assert parse_next_link(header) == "https://canvas.example/api/v1/users/self/todo?page=2"


def test_parse_next_link_returns_none_without_next():
    header = '<https://canvas.example/api/v1/users/self/todo?page=1>; rel="current"'

    assert parse_next_link(header) is None
