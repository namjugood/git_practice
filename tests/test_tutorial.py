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
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 1: identity (git config) -- must be real values, not the shown placeholder
    tutorial.describe_current_step(ws)
    ok, _ = tutorial.check_current_step(ws)
    assert not ok, "placeholder should not have been configured yet, so this must still fail"
    g.run(["config", "user.name", "Test User"], cwd=ws.repo_dir)
    g.run(["config", "user.email", "test@example.com"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 2: first commit
    tutorial.describe_current_step(ws)
    g.write_file(ws.repo_dir, "hello.txt", "hello git\n")
    g.add_all(ws.repo_dir)
    g.commit(ws.repo_dir, "my first commit")
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 3: branch (learner picks any name)
    tutorial.describe_current_step(ws)
    g.run(["checkout", "-b", "my-own-branch-name"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok
    assert ws.get("practice_branch") == "my-own-branch-name"

    # step 4: branch commit
    tutorial.describe_current_step(ws)
    g.append_file(ws.repo_dir, "hello.txt", "branch work\n")
    g.add_all(ws.repo_dir)
    g.commit(ws.repo_dir, "work on my branch")
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 5: merge (template mode, references the remembered branch name)
    step_text = tutorial.describe_current_step(ws)
    assert "my-own-branch-name" in step_text
    g.run(["checkout", "main"], cwd=ws.repo_dir)
    g.run(["merge", "my-own-branch-name", "--no-edit"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 6: remote + push (compose mode; on_enter creates the bare remote)
    tutorial.describe_current_step(ws)
    assert ws.remote_dir.exists()
    g.run(["remote", "add", "origin", str(ws.remote_dir)], cwd=ws.repo_dir)
    g.run(["push", "-u", "origin", "main"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    # step 7: pull (on_enter injects a teammate commit into origin)
    tutorial.describe_current_step(ws)
    assert ws.get("teammate_marker_commit")
    g.run(["pull", "origin", "main"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert ok

    assert ws.get("completed") is True
    assert "완료" in tutorial.describe_current_step(ws)


def test_identity_placeholder_is_rejected(tmp_path):
    ws = tutorial.start_new(base_dir=tmp_path)
    g.run(["init", "-q", "-b", "main"], cwd=ws.repo_dir)
    tutorial.check_current_step(ws)

    g.run(["config", "user.name", tutorial.PLACEHOLDER_NAME], cwd=ws.repo_dir)
    g.run(["config", "user.email", f"{tutorial.PLACEHOLDER_EMAIL}@example.com"], cwd=ws.repo_dir)
    ok, _ = tutorial.check_current_step(ws)
    assert not ok, "leaving the example placeholder text in place must not pass"
