from pathlib import Path


def test_missing_projects_root_rebinds_to_this_users_synced_library(monkeypatch, tmp_path):
    import app.core.config as config

    current = tmp_path / "Juma Al Majid" / "SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
    current.mkdir(parents=True)
    monkeypatch.setattr(config, "find_synced_folder", lambda name: str(current))
    settings = config.Settings(_env_file=None, projects_root=str(tmp_path / "old-user" / current.name),
                               projects_root_autodetect=True)
    assert Path(settings.projects_root) == current


def test_reachable_explicit_projects_root_is_kept(monkeypatch, tmp_path):
    import app.core.config as config

    configured = tmp_path / "configured"
    configured.mkdir()
    monkeypatch.setattr(config, "find_synced_folder", lambda name: str(tmp_path / "other"))
    settings = config.Settings(_env_file=None, projects_root=str(configured), projects_root_autodetect=True)
    assert Path(settings.projects_root) == configured


def test_missing_explicit_root_is_preserved_when_no_synced_library_is_found(monkeypatch, tmp_path):
    import app.core.config as config

    missing = tmp_path / "missing"
    monkeypatch.setattr(config, "find_synced_folder", lambda name: None)
    settings = config.Settings(_env_file=None, projects_root=str(missing), projects_root_autodetect=True)
    assert Path(settings.projects_root) == missing
