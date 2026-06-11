from hermes_bridge.desktop_actions import (
    DesktopActionRunner,
    parse_desktop_action,
    parse_reply_action,
)


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


def test_parse_reply_action_opens_agent_browser_navigate_url():
    action = parse_reply_action('browser_navigate: "https://www.youtube.com/"')

    assert action is not None
    assert action.kind == "url"
    assert action.target == "https://www.youtube.com/"


def test_parse_reply_action_opens_done_reply_url():
    action = parse_reply_action("Done bre, YouTube udah kebuka: https://www.youtube.com/")

    assert action is not None
    assert action.kind == "url"
    assert action.target == "https://www.youtube.com/"


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


def test_desktop_action_runner_can_run_agent_reply_action():
    opened_urls = []
    runner = DesktopActionRunner(open_url=opened_urls.append)

    result = runner.run_reply('browser_navigate: "https://www.youtube.com/"')

    assert result.handled is True
    assert result.message == "Opened https://www.youtube.com/."
    assert opened_urls == ["https://www.youtube.com/"]
