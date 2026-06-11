from hermes_bridge.ui.main_window import should_hide_instead_of_close


def test_should_hide_instead_of_close_only_in_voice_mode():
    assert should_hide_instead_of_close(True) is True
    assert should_hide_instead_of_close(False) is False
