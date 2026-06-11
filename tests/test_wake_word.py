import pytest

from hermes_bridge.voice.wake_word import wake_score


def test_wake_score_matches_alias_or_model_stem():
    matched, model_name, score = wake_score(
        {
            "hey_hermes": 0.76,
            "alexa": 0.91,
        },
        aliases=("hey hermes", "hermes"),
        threshold=0.7,
    )

    assert matched is True
    assert model_name == "hey_hermes"
    assert score == pytest.approx(0.76)


def test_wake_score_matches_versioned_model_name():
    matched, model_name, score = wake_score(
        {
            "hey_hermes_cnn_v1": 0.81,
        },
        aliases=("hey hermes", "hermes"),
        threshold=0.7,
    )

    assert matched is True
    assert model_name == "hey_hermes_cnn_v1"
    assert score == pytest.approx(0.81)


def test_wake_score_accepts_array_scores():
    matched, model_name, score = wake_score(
        {
            "hey_hermes_cnn_v1": [0.12, 0.42],
        },
        aliases=("hey hermes", "hermes"),
        threshold=0.35,
    )

    assert matched is True
    assert model_name == "hey_hermes_cnn_v1"
    assert score == pytest.approx(0.42)


def test_wake_score_ignores_unconfigured_models():
    matched, model_name, score = wake_score(
        {
            "hey_hermes": 0.49,
            "alexa": 0.95,
        },
        aliases=("hey hermes", "hermes"),
        threshold=0.5,
    )

    assert matched is False
    assert model_name == ""
    assert score == 0.0
