"""R31-01 selector rules on synthetic folder trees (no real document). Run: python -m pytest -q test_selector_core.py"""
import selector_core as S


def tree(tmp_path, dirs):
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return str(tmp_path)


def test_canonical_names_drop_qualifiers_and_legal_suffixes():
    assert S.canon("Al Arabia EMW (Old Projects)") == S.canon("Al Arabia EMW") == "al arabia emw"
    assert S.canon("Euro Gulf Technoservices LLC") == "euro gulf technoservices"
    assert S.canon("Abc & Co. L.L.C") == "abc"


def test_aliases_are_fail_closed():
    assert S.aliases(S.canon("Al Yunbou EMW"), S.canon("Al Yunbou Technical")), "same distinctive first word"
    assert S.aliases(S.canon("Bin Ladin"), S.canon("Binladin")), "space-free equal"
    assert S.aliases(S.canon("Naffco"), S.canon("NAFFCO FZCO")), "legal suffix"
    assert S.aliases(S.canon("Trikon Electromechanical"), S.canon("Trikon")), "token subset"
    assert not S.aliases(S.canon("ENCO"), S.canon("GECO"))
    assert not S.aliases(S.canon("Al Abdouli Group"), S.canon("Al Abiya"))


def test_topology_classification_and_ambiguity(tmp_path):
    root = tree(tmp_path, ["EP-11111 - project at root/x", "Maintenance/EP-50001 - in a container", "Contractor A/EP-60001 - ok",
                           "Contractor A/Archive/EP-60002 - nested", "Contractor B/EP-60003 - parent/EP-60004 - child",
                           "Contractor C/EP-60005 - one", "Contractor C (Old Projects)/EP-60005 - two", "Empty Contractor/notes"])
    topo, projects, amb = S.classify(root, {"Maintenance"})
    assert topo["project_at_root"] == 1 and topo["container"] == 1 and topo["no_projects"] == 1
    classes = {a["ep"]: a["class"] for a in amb}
    assert classes["11111"] == "project_at_root" and classes["60002"] == "nested_project" and classes["60003"] == "project_with_nested_eps"
    _clusters, cluster_of = S.cluster(sorted({p["contractor"] for ps in projects.values() for p in ps}))
    fresh = S.fresh_projects(projects, amb, cluster_of, used_eps=set(), containers={"Maintenance"})
    assert set(fresh) == {"60001"}, "nested, parent-of-nested, multi-folder (60005 in two alias folders) and container projects are excluded"


def test_a_used_ep_is_never_fresh(tmp_path):
    root = tree(tmp_path, ["Contractor A/EP-60001 - ok", "Contractor D/EP-60006 - ok"])
    _t, projects, amb = S.classify(root)
    _c, cluster_of = S.cluster(sorted({p["contractor"] for ps in projects.values() for p in ps}))
    assert set(S.fresh_projects(projects, amb, cluster_of, used_eps={"60006"})) == {"60001"}
