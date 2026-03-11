from __future__ import annotations

import pytest

from crepe import cli


class DummyRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def run_extract(self, run_id=None, scope=None):
        self.calls.append(("extract", run_id))
        return run_id or "extract-run"

    def run_normalize(self, run_id):
        self.calls.append(("normalize", run_id))
        return run_id

    def run_analyze(self, run_id):
        self.calls.append(("analyze", run_id))
        return run_id

    def run_suggest(self, run_id):
        self.calls.append(("suggest", run_id))
        return run_id

    def run_all(self, run_id=None, scope=None):
        self.calls.append(("all", run_id))
        return run_id or "all-run"

    def run_demo(self, run_id=None, scope=None):
        self.calls.append(("demo", run_id))
        return run_id or "demo-run"


@pytest.mark.unit
def test_cli_dispatches_to_demo(monkeypatch, capsys):
    dummy_runner = DummyRunner()
    monkeypatch.setattr(cli, "load_config", lambda *args, **kwargs: type("Cfg", (), {"db_path": "x", "log_level": "INFO"})())
    monkeypatch.setattr(cli, "configure_logging", lambda *_: None)
    monkeypatch.setattr(cli, "RunDatabase", lambda *_: object())
    monkeypatch.setattr(cli, "PipelineRunner", lambda *_: dummy_runner)
    monkeypatch.setattr("sys.argv", ["crepe", "demo", "--run-id", "r1"])
    cli.main()
    out = capsys.readouterr().out.strip()
    assert out == "r1"
    assert dummy_runner.calls == [("demo", "r1")]


@pytest.mark.unit
def test_cli_requires_run_id_for_normalize(monkeypatch):
    monkeypatch.setattr("sys.argv", ["crepe", "normalize"])
    parser = cli.build_parser()
    args = parser.parse_args()
    assert args.command == "normalize"
    monkeypatch.setattr(cli, "load_config", lambda *args, **kwargs: type("Cfg", (), {"db_path": "x", "log_level": "INFO"})())
    monkeypatch.setattr(cli, "configure_logging", lambda *_: None)
    monkeypatch.setattr(cli, "RunDatabase", lambda *_: object())
    monkeypatch.setattr(cli, "PipelineRunner", lambda *_: DummyRunner())
    with pytest.raises(SystemExit):
        cli.main()
