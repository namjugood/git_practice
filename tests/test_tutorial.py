import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gitsim import gitutil as g
from gitsim import tutorial


def test_tutorial_full_walkthrough(tmp_path):
    ws = tutorial.start_new(base_dir=tmp_path)

    # step 0: init
    tutorial.describe_current_step(ws)
    g.run(["init", "-q", "-b", "main"], cwd=ws.repo_dir)
    g.configure_identity(ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 1: first commit
    tutorial.describe_current_step(ws)
    g.write_file(ws.repo_dir, "hello.txt", "hello git\n")
    g.add_all(ws.repo_dir)
    g.commit(ws.repo_dir, "첫 커밋")
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 2: branch
    tutorial.describe_current_step(ws)
    g.run(["checkout", "-b", "practice-branch"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 3: branch commit
    tutorial.describe_current_step(ws)
    g.append_file(ws.repo_dir, "hello.txt", "branch work\n")
    g.add_all(ws.repo_dir)
    g.commit(ws.repo_dir, "브랜치 작업")
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 4: merge
    tutorial.describe_current_step(ws)
    g.run(["checkout", "main"], cwd=ws.repo_dir)
    g.run(["merge", "practice-branch", "--no-edit"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 5: remote + push (on_enter creates the bare remote)
    tutorial.describe_current_step(ws)
    assert ws.remote_dir.exists()
    g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
    g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 6: pull (on_enter injects a teammate commit into origin)
    tutorial.describe_current_step(ws)
    assert ws.get("teammate_marker_commit")
    g.run(["pull", "origin", "main"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    assert ws.get("completed") is True
    assert "완료" in tutorial.describe_current_step(ws)
