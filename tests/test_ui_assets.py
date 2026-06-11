from hermes_bridge.ui.assets import resolve_asset_path


def test_resolve_asset_path_points_to_project_root_file():
    path = resolve_asset_path("hermes-logo.png")

    assert path.name == "hermes-logo.png"
    assert path.parent.name == "Hermes-Voice"
