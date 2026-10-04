from pathlib import Path


def test_rebinds_only_existing_relative_project_folders(db_session, tmp_path, monkeypatch):
    from app.models import Project, User
    from app.services import ep_directory

    archive = tmp_path / "current" / "SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
    present = archive / "Contractor" / "EP-40001 Tower"
    present.mkdir(parents=True)
    old_root = Path("C:/Users/old/Juma Al Majid") / archive.name
    user_id = db_session.query(User).first().id
    moved = Project(ep_number="40001", project_name="Tower",
                    source_folder_path=str(old_root / "Contractor" / "EP-40001 Tower"), created_by_id=user_id)
    missing = Project(ep_number="40002", project_name="Missing",
                      source_folder_path=str(old_root / "Contractor" / "EP-40002 Missing"), created_by_id=user_id)
    unrelated = Project(ep_number="40003", project_name="Outside",
                        source_folder_path="C:/somewhere/EP-40003", created_by_id=user_id)
    db_session.add_all([moved, missing, unrelated]); db_session.commit()

    monkeypatch.setattr(ep_directory, "get_settings",
                        lambda: type("S", (), {"projects_root_name": archive.name})())
    changed = ep_directory.rebind_project_paths(db_session, archive)

    assert changed == [("40001", str(present.resolve()))]
    assert Path(moved.source_folder_path) == present.resolve()
    assert Path(missing.source_folder_path) == old_root / "Contractor" / "EP-40002 Missing"
    assert unrelated.source_folder_path == "C:/somewhere/EP-40003"


def test_rebind_keeps_an_existing_explicit_project_path(db_session, tmp_path, monkeypatch):
    from app.models import Project, User
    from app.services import ep_directory

    archive = tmp_path / "archive"
    archive.mkdir()
    existing = tmp_path / "separate-project"
    existing.mkdir()
    row = Project(ep_number="40004", project_name="Separate", source_folder_path=str(existing),
                  created_by_id=db_session.query(User).first().id)
    db_session.add(row); db_session.commit()
    monkeypatch.setattr(ep_directory, "get_settings",
                        lambda: type("S", (), {"projects_root_name": archive.name})())
    assert ep_directory.rebind_project_paths(db_session, archive) == []
    assert Path(row.source_folder_path) == existing
