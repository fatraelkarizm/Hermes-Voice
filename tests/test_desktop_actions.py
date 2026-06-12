from hermes_bridge.desktop_actions import (
    AppCandidate,
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


def test_parse_desktop_action_opens_dynamic_start_menu_match():
    action = parse_desktop_action(
        "bukain spotify",
        app_candidates=(
            AppCandidate(name="Spotify", target="C:/Start Menu/Spotify.lnk"),
        ),
    )

    assert action is not None
    assert action.kind == "app"
    assert action.name == "Spotify"
    assert action.target == "C:/Start Menu/Spotify.lnk"


def test_parse_desktop_action_uses_common_alias_for_dynamic_match():
    action = parse_desktop_action(
        "buka vscode",
        app_candidates=(
            AppCandidate(name="Visual Studio Code", target="C:/Start Menu/Code.lnk"),
        ),
    )

    assert action is not None
    assert action.kind == "app"
    assert action.name == "Visual Studio Code"


def test_parse_desktop_action_asks_when_dynamic_match_is_ambiguous():
    action = parse_desktop_action(
        "open code",
        app_candidates=(
            AppCandidate(name="Visual Studio Code", target="Code.lnk"),
            AppCandidate(name="CodeBlocks", target="CodeBlocks.lnk"),
        ),
    )

    assert action is not None
    assert action.kind == "app_ambiguous"
    assert action.name == "Visual Studio Code, CodeBlocks"


def test_parse_desktop_action_deduplicates_same_dynamic_app_name():
    action = parse_desktop_action(
        "open vscode",
        app_candidates=(
            AppCandidate(name="Visual Studio Code", target="User/Code.lnk"),
            AppCandidate(name="Visual Studio Code", target="System/Code.lnk"),
        ),
    )

    assert action is not None
    assert action.kind == "app"
    assert action.name == "Visual Studio Code"
    assert action.target == "User/Code.lnk"


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


def test_desktop_action_runner_returns_ambiguity_message_without_opening():
    opened_apps = []
    runner = DesktopActionRunner(
        open_app=opened_apps.append,
        app_candidates=(
            AppCandidate(name="Visual Studio Code", target="Code.lnk"),
            AppCandidate(name="CodeBlocks", target="CodeBlocks.lnk"),
        ),
    )

    result = runner.run("open code")

    assert result.handled is True
    assert result.message == "Which app should I open: Visual Studio Code, CodeBlocks?"
    assert opened_apps == []
