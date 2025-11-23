"""Suite runner to execute request suites defined via -s/--suite."""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import csv

from .args import PurlArgs
from .output import ColoredOutput
from .request_runner import RequestRunner
from .yaml_reader import read_and_parse_yaml
from .reporters.html_reporter import SuiteHtmlReporter


class SuiteRunner:
    """Loads suite YAML files, including optional CSV data sources, and runs request files."""

    def __init__(self):
        self.args = PurlArgs()

    def run(self) -> List[Dict[str, Any]]:
        if not self.args.suite_file:
            return []

        suite_path = Path(self.args.suite_file)
        if not suite_path.exists():
            ColoredOutput.error(f"Suite file not found: {suite_path}")
            return []

        suite_data = read_and_parse_yaml(str(suite_path)) or {}
        suite_dir = suite_path.parent

        self._apply_suite_configs(suite_data)
        self._apply_suite_variables(suite_data)
        self._apply_suite_options(suite_data)

        request_files = self._resolve_requests(suite_data, suite_dir)
        data_rows = self._load_data_rows(suite_data, suite_dir)

        aggregated_results: List[Dict[str, Any]] = []

        for row_index, row in enumerate(data_rows, start=1):
            if len(data_rows) > 1:
                ColoredOutput.separator("-", 80, "cyan")
                ColoredOutput.header(f"SUITE ROW {row_index}/{len(data_rows)}")

            self._apply_row_variables(row)
            self.args.request_files = request_files
            runner = RequestRunner()
            run_results = runner.run()

            if isinstance(run_results, tuple):  # No request files / error fallback
                run_results = []

            aggregated_results.append({
                "row_index": row_index,
                "variables": row,
                "requests": run_results
            })

        reporter = SuiteHtmlReporter(suite_data.get("Name", suite_path.stem), self._get_working_dir())
        report_file_path = suite_data.get("ReportPath")
        report_path = reporter.generate(aggregated_results, report_file_path)

        ColoredOutput.info(f"Suite report generated: {report_path}")
        return aggregated_results

    def _apply_suite_configs(self, suite_data: Dict[str, Any]):
        suite_configs = suite_data.get("Configs") or []
        if suite_configs:
            self.args.config_names = suite_configs + self.args.config_names

    def _apply_suite_variables(self, suite_data: Dict[str, Any]):
        suite_vars = suite_data.get("Vars") or {}
        if isinstance(suite_vars, dict):
            normalized = {str(k): str(v) for k, v in suite_vars.items()}
            normalized.update(self.args.variables or {})
            self.args.variables = normalized

    def _apply_suite_options(self, suite_data: Dict[str, Any]):
        options = suite_data.get("Options") or {}
        if self.args.timeout is None and "timeout" in options:
            self.args.timeout = options["timeout"]
        if options.get("insecure"):
            self.args.insecure = True

    def _resolve_requests(self, suite_data: Dict[str, Any], suite_dir: Path) -> List[str]:
        request_entries = suite_data.get("Requests") or []
        resolved: List[str] = []
        for entry in request_entries:
            path = Path(str(entry))
            if not path.is_absolute():
                path = (suite_dir / path).resolve()
            resolved.append(str(path))
        return resolved

    def _load_data_rows(self, suite_data: Dict[str, Any], suite_dir: Path) -> List[Dict[str, Any]]:
        data_source = suite_data.get("DataSources")
        if not data_source:
            return [{}]

        if isinstance(data_source, str):
            sources = [data_source]
        elif isinstance(data_source, list):
            sources = data_source
        else:
            raise ValueError("DataSources must be a string or list of strings")

        if len(sources) != 1:
            raise ValueError("Only a single CSV data source is supported currently")

        csv_path = Path(str(sources[0]))
        if not csv_path.is_absolute():
            csv_path = (suite_dir / csv_path).resolve()

        rows: List[Dict[str, Any]] = []
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append({k: v for k, v in row.items() if k})

        return rows or [{}]

    def _apply_row_variables(self, row: Dict[str, Any]):
        row_vars = {str(k): '' if v is None else str(v) for k, v in row.items()}
        base_vars = self.args.variables or {}
        combined = {**base_vars, **row_vars}
        self.args.variables = combined

    def _get_working_dir(self) -> Path:
        if self.args.working_dir:
            return Path(self.args.working_dir)
        return Path.cwd()
