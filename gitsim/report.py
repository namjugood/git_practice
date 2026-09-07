"""`gitsim check` 결과를 실제 git 산출물과 함께 markdown 리포트로 정리한다."""

from __future__ import annotations

import time

from gitsim import gitutil as g
from gitsim.i18n import t
from gitsim.scenarios.base import CheckResult, Scenario
from gitsim.workspace import Workspace


def build_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status_line = t("report.status.success") if result.success else t("report.status.pending")
    log_graph = g.log_graph(ws.repo_dir) or t("report.no_log")
    reflog_text = g.reflog(ws.repo_dir) or t("report.no_reflog")
    remote_log = ""
    if ws.remote_dir.exists():
        remote_log = g.log_graph(ws.remote_dir) or t("report.no_remote_log")

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


def write_report(scenario: Scenario, ws: Workspace, result: CheckResult, diagnosis: list[str]) -> None:
    ws.report_file.write_text(build_report(scenario, ws, result, diagnosis), encoding="utf-8")
