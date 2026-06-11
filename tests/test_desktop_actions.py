from hermes_bridge.desktop_actions import DesktopActionRunner, parse_desktop_action


def test_parse_desktop_action_opens_known_website():
    action = parse_desktop_action("open youtube")

    assert action is not None
    assert action.kind == "url"
    assert action.target == "https://www.youtube.com"


def test_parse_desktop_action_accepts_indonesian_buka():
    action = parse_desktop_action("buka google")

    assert action is not None
    assert action.kind == "url"
    assert action.target == "https://www.google.com"


def test_parse_desktop_action_opens_known_app():
    action = parse_desktop_action("open discord")

    assert action is not None
    assert action.kind == "app"
    assert action.target == "discord"


def test_parse_desktop_action_rejects_unknown_commands():
    assert parse_desktop_action("delete system32") is None


def test_desktop_action_runner_uses_injected_openers():
    opened_urls = []
    opened_apps = []
    runner = DesktopActionRunner(
        open_url=opened_urls.append,
        open_app=opened_apps.append,
    )

    result = runner.run("open youtube")

    assert result.handled is True
    assert result.message == "Opening YouTube."
    assert opened_urls == ["https://www.youtube.com"]
    assert opened_apps == []
