import pandas as pd

from scripts.wm811k.manifests import build_manifests


def make_frame() -> pd.DataFrame:
    labels = ["center"] * 100 + ["scratch"] * 30 + ["none"] * 50
    return pd.DataFrame({"failure_type": labels})


def test_manifests_are_disjoint() -> None:
    manifests = build_manifests(make_frame(), seed=42)
    calibration = set(manifests["calibration"])
    eval_set = set(manifests["eval"])
    pool = set(manifests["fewshot_pool"])

    assert not calibration & eval_set
    assert not calibration & pool
    assert not eval_set & pool


def test_caps_and_reserves_respected() -> None:
    manifests = build_manifests(
        make_frame(),
        seed=42,
        eval_cap=40,
        calibration_per_class=10,
        fewshot_reserve=20,
        none_eval=25,
    )
    frame = make_frame()

    def count(manifest: str, name: str) -> int:
        return sum(
            1
            for index in manifests[manifest]
            if frame.loc[index, "failure_type"] == name
        )

    assert count("calibration", "center") == 10
    assert count("fewshot_pool", "center") == 20
    assert count("eval", "center") == 40
    assert count("calibration", "scratch") == 3
    assert count("fewshot_pool", "scratch") == 12
    assert count("eval", "scratch") == 15


def test_none_split_between_calibration_and_eval() -> None:
    manifests = build_manifests(
        make_frame(), seed=42, none_calibration=10, none_eval=25
    )
    frame = make_frame()

    none_indices = set(frame.index[frame["failure_type"] == "none"])
    assert len(none_indices & set(manifests["calibration"])) == 10
    assert len(none_indices & set(manifests["eval"])) == 25
    assert not none_indices & set(manifests["fewshot_pool"])


def test_deterministic_under_seed() -> None:
    assert build_manifests(make_frame(), seed=7) == build_manifests(
        make_frame(), seed=7
    )
