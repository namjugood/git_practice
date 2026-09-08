"""`gitsim check` 결과를 실제 git 산출물과 함께 markdown 리포트로 정리한다."""

from __future__ import annotations

import time
from typing import Optional

from gitsim import gitutil as g
from gitsim.i18n import t
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace, get_remote_url, practice_branch_name


def build_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status_line = t("report.status.success") if result.success else t("report.status.pending")
    log_graph = g.log_graph(ws.repo_dir) or t("report.no_log")
    reflog_text = g.reflog(ws.repo_dir) or t("report.no_reflog")
    remote_log = t("report.no_remote_log")
    if (ws.repo_dir / ".git").exists():
        g.run(["fetch", "origin"], cwd=ws.repo_dir, check=False)
        if g.rev_parse(ws.repo_dir, "origin/main"):
            proc = g.run(
                ["log", "--graph", "--oneline", "--decorate", "origin/main", "-30"],
                cwd=ws.repo_dir,
                check=False,
            )
            remote_log = proc.stdout or t("report.no_remote_log")

    details_block = "\n".join(f"- {d}" for d in result.details) or f"- {t('report.no_details')}"
    diagnosis_block = "\n".join(f"- {d}" for d in diagnosis) or f"- {t('report.no_diagnosis')}"

    return t(
        "report.body",
        title=scenario.title,
        scenario_id=scenario.id,
        level=scenario.level,
        timestamp=timestamp,
        workspace_path=ws.path,
        status_line=status_line,
        summary=result.summary,
        details_block=details_block,
        briefing=scenario.briefing(ws),
        log_graph=log_graph,
        reflog_text=reflog_text,
        remote_log=remote_log,
        diagnosis_block=diagnosis_block,
        model_answer=scenario.model_answer(ws),
        concepts=scenario.concepts(ws),
    )


def write_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> str:
    """리포트를 만들어 REPORT.md로 저장하고, 만든 텍스트를 그대로 돌려준다.

    호출자가 이 텍스트를 `publish_report()`에 그대로 넘기면, 원격에 한 번 더 fetch해서
    리포트를 처음부터 다시 만드는(그리고 시각이 미묘하게 달라지는) 중복 작업을 피할 수 있다.
    """
    report_text = build_report(scenario, ws, result, diagnosis)
    ws.report_file.write_text(report_text, encoding="utf-8")
    return report_text


def publish_report(ws: Workspace, report_text: str, result: CheckResult) -> Optional[str]:
    """검사에 성공했을 때만, `report_text`를 README.md로 이 워크스페이스의 연습 브랜치에 push한다.

    실패한 시도에서는 push하지 않는다 — 학습자가 아직 로컬에서 같은 브랜치를 계속 고쳐나가는
    중일 수 있는데, 원격에 학습자 모르게 새 커밋(README.md)을 얹어두면 이후 학습자의
    `git push`가 non-fast-forward로 거부되는 상황을 만들 수 있기 때문이다.

    학습자의 실제 작업 저장소(`ws.repo_dir`)는 건드리지 않도록, 별도의 임시 클론에서
    README.md만 커밋하고 push한 뒤 바로 지운다. 등록된 원격이 없으면 아무 일도 하지 않는다.
    리포트 내용은 `write_report()`가 이미 만든 텍스트를 그대로 받아서 쓴다 — 원격에 다시
    fetch해서 리포트를 처음부터 새로 만들지 않는다.
    """
    if not result.success:
        return None
    remote_url = get_remote_url()
    if not remote_url:
        return None

    branch = practice_branch_name(ws)
    tmp_dir = ws.path / "_report_publish_tmp"
    if tmp_dir.exists():
        g.force_rmtree(tmp_dir)
    try:
        g.init_repo(tmp_dir)
        g.run(["remote", "add", "origin", remote_url], cwd=tmp_dir)
        fetch_proc = g.run(["fetch", "origin", branch], cwd=tmp_dir, check=False)
        if fetch_proc.returncode == 0 and g.rev_parse(tmp_dir, "FETCH_HEAD"):
            g.run(["checkout", "-B", branch, "FETCH_HEAD"], cwd=tmp_dir)
        else:
            g.run(["checkout", "-b", branch], cwd=tmp_dir)

        g.write_file(tmp_dir, "README.md", report_text)
        g.add_all(tmp_dir)
        if not g.status_porcelain(tmp_dir).strip():
            return branch

        g.commit(tmp_dir, t("report.publish_commit_message"))
        g.run(["push", "origin", f"HEAD:{branch}"], cwd=tmp_dir)
        return branch
    finally:
        if tmp_dir.exists():
            g.force_rmtree(tmp_dir)
