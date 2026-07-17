"""Suite runner to execute request suites defined via -s/--suite."""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import csv

import yaml

from .args import PurlArgs
from .output import ColoredOutput
from .request_processor import RequestProcessor
from .variables import VariableContext
from .reporters.html_reporter import SuiteHtmlReporter


@dataclass
class RequestSource:
    """A single request to run within a suite - either a file on disk or an
    in-memory ``Kind: Request`` document embedded in the suite file."""
    label: str
    file_path: Optional[str] = None
    raw_yaml: Optional[str] = None


@dataclass
class SuitePlan:
    """Normalized, ready-to-execute view of a 'Kind: Suite' document."""
    name: str
    report_path: Optional[str]
    file_config_names: List[str] = field(default_factory=list)
    embedded_configs: List[Dict[str, Any]] = field(default_factory=list)
    suite_vars: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    data_rows: List[Dict[str, Any]] = field(default_factory=list)
    requests: List[RequestSource] = field(default_factory=list)


# Map of Kind -> {Name -> (raw_text, parsed)} for documents embedded in a suite file
DocGroups = Dict[str, Dict[str, Tuple[str, Dict[str, Any]]]]


class SuiteRunner:
    """Loads a 'Kind: Suite' YAML file and runs its requests, then generates an HTML report.

    A suite file is a (possibly multi-document) YAML file containing exactly
    one ``Kind: Suite`` document plus, optionally, ``Kind: Request``,
    ``Kind: Configs`` and ``Kind: DataSet`` documents alongside it.

    The suite document's ``Requests``, ``Configs`` and ``DataSet`` fields each
    reference either:
      * an embedded document of the matching Kind in the same file (by ``Name``), or
      * an external file (a request YAML file, a config YAML file, or a
        DataSet as CSV/YAML), resolved relative to the suite file's directory.
    """

    def __init__(self):
        self.args = PurlArgs()
        self.processor = RequestProcessor()

    def run(self) -> bool:
        """Run the configured suite and generate its HTML report.

        Returns:
            True if every request executed without error and every assertion
            passed, False otherwise.
        """
        if not self.args.suite_file:
            ColoredOutput.error("No suite file provided")
            return False

        suite_path = Path(self.args.suite_file)
        if not suite_path.exists():
            ColoredOutput.error(f"Suite file not found: {suite_path}")
            return False

        suite_dir = suite_path.parent
        documents = self._split_documents(suite_path.read_text(encoding="utf-8"))

        if not documents:
            ColoredOutput.error(f"Suite file is empty: {suite_path}")
            return False

        try:
            plan = self._build_plan(documents, suite_dir, default_name=suite_path.stem)
        except ValueError as err:
            ColoredOutput.error(f"Invalid suite file {suite_path}: {err}")
            return False

        return self._execute_plan(plan)

    # ------------------------------------------------------------------
    # YAML document splitting
    # ------------------------------------------------------------------

    def _split_documents(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Split a (possibly multi-document) YAML file into (raw_text, parsed) pairs.

        Raw text per document is preserved (via composer node marks, not naive
        '---' string splitting) so embedded ``Kind: Request`` documents can be
        fed through the same variable-resolution pipeline used for request
        files, which substitutes '${...}' placeholders in raw text before
        parsing.
        """
        loader = yaml.SafeLoader(text)
        docs: List[Tuple[str, Dict[str, Any]]] = []
        try:
            while loader.check_node():
                node = loader.get_node()
                if node is None:
                    continue
                raw_doc = text[node.start_mark.index:node.end_mark.index]
                parsed = loader.construct_document(node)
                if parsed:
                    docs.append((raw_doc, parsed))
        finally:
            loader.dispose()
        return docs

    # ------------------------------------------------------------------
    # Plan building
    # ------------------------------------------------------------------

    def _build_plan(self, documents: List[Tuple[str, Dict[str, Any]]], suite_dir: Path, default_name: str) -> SuitePlan:
        grouped: DocGroups = defaultdict(dict)
        for raw, parsed in documents:
            kind = str(parsed.get("Kind", "Unknown"))
            name = str(parsed.get("Name") or f"{kind}_{len(grouped[kind]) + 1}")
            grouped[kind][name] = (raw, parsed)

        suite_entries = grouped.get("Suite", {})
        if not suite_entries:
            raise ValueError("No 'Kind: Suite' document found")
        _, (_, suite_data) = next(iter(suite_entries.items()))

        requests = self._resolve_requests(suite_data.get("Requests") or [], grouped, suite_dir)
        data_rows = self._resolve_dataset(suite_data.get("DataSet"), grouped, suite_dir)
        file_config_names, embedded_configs = self._resolve_configs(suite_data.get("Configs") or [], grouped, suite_dir)

        return SuitePlan(
            name=suite_data.get("Name") or default_name,
            report_path=suite_data.get("ReportPath"),
            file_config_names=file_config_names,
            embedded_configs=embedded_configs,
            suite_vars=suite_data.get("Vars") or {},
            options=suite_data.get("Options") or {},
            data_rows=data_rows,
            requests=requests,
        )

    def _resolve_path(self, entry: str, suite_dir: Path) -> Path:
        path = Path(entry)
        if not path.is_absolute():
            path = (suite_dir / path).resolve()
        return path

    def _resolve_requests(self, names: List[str], grouped: DocGroups, suite_dir: Path) -> List[RequestSource]:
        requests: List[RequestSource] = []
        for name in names:
            entry = grouped.get("Request", {}).get(str(name))
            if entry:
                raw, _ = entry
                requests.append(RequestSource(label=str(name), raw_yaml=raw))
                continue

            path = self._resolve_path(str(name), suite_dir)
            if not path.exists():
                raise ValueError(
                    f"Requests entry '{name}' is neither an embedded 'Kind: Request' document "
                    f"nor an existing file ({path})"
                )
            requests.append(RequestSource(label=str(path), file_path=str(path)))
        return requests

    def _resolve_dataset(self, dataset_ref: Optional[str], grouped: DocGroups, suite_dir: Path) -> List[Dict[str, Any]]:
        if not dataset_ref:
            return [{}]

        entry = grouped.get("DataSet", {}).get(str(dataset_ref))
        if entry:
            _, dataset_doc = entry
            return dataset_doc.get("Data") or [{}]

        path = self._resolve_path(str(dataset_ref), suite_dir)
        if not path.exists():
            raise ValueError(
                f"DataSet '{dataset_ref}' is neither an embedded 'Kind: DataSet' document "
                f"nor an existing file ({path})"
            )

        if path.suffix.lower() == ".csv":
            return self._load_csv_rows(path)

        content = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if isinstance(content, list):
            return content or [{}]
        if isinstance(content, dict):
            return content.get("Data") or [{}]
        raise ValueError(f"DataSet file {path} must contain a list of rows or a mapping with a 'Data' key")

    def _resolve_configs(self, names: List[str], grouped: DocGroups, suite_dir: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        file_config_names: List[str] = []
        embedded_configs: List[Dict[str, Any]] = []

        for name in names:
            entry = grouped.get("Configs", {}).get(str(name))
            if entry:
                _, config_doc = entry
                embedded_configs.append(config_doc.get("Configs") or {})
                continue

            path = self._resolve_path(str(name), suite_dir)
            if path.exists():
                content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if isinstance(content, dict) and content.get("Kind") == "Configs":
                    embedded_configs.append(content.get("Configs") or {})
                elif isinstance(content, dict):
                    embedded_configs.append(content)
                else:
                    raise ValueError(f"Config file {path} must contain a YAML mapping")
                continue

            # Not an embedded document or an existing file - treat as a config
            # name to be loaded from the project's configured configs directory.
            file_config_names.append(str(name))

        return file_config_names, embedded_configs

    def _load_csv_rows(self, csv_path: Path) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append({k: v for k, v in row.items() if k})
        return rows or [{}]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _execute_plan(self, plan: SuitePlan) -> bool:
        var_context = VariableContext()

        # Configs: file-based names (existing '-c' style loading) first, then
        # embedded/external config documents appended with higher priority.
        var_context.load_configs(plan.file_config_names)
        var_context.configs.extend(plan.embedded_configs)

        self._apply_suite_options(plan.options)

        self.processor.initialize()

        ColoredOutput.separator("=", 80, "magenta")
        ColoredOutput.header(f"SUITE: {plan.name}")
        if plan.file_config_names:
            ColoredOutput.env_config(plan.file_config_names)
        if plan.embedded_configs:
            ColoredOutput.info(f"Embedded/external configs applied: {len(plan.embedded_configs)}")
        ColoredOutput.separator("=", 80, "magenta")

        aggregated_results: List[Dict[str, Any]] = []
        all_passed = True

        for row_index, row in enumerate(plan.data_rows, start=1):
            if len(plan.data_rows) > 1:
                ColoredOutput.separator("-", 80, "cyan")
                ColoredOutput.header(f"SUITE ROW {row_index}/{len(plan.data_rows)}")

            self._apply_row_variables(var_context, plan.suite_vars, row)

            run_results: List[Dict[str, Any]] = []
            for req_index, source in enumerate(plan.requests, start=1):
                result = self._run_single_request(source, req_index, len(plan.requests))
                run_results.append(result)
                if not self._request_passed(result):
                    all_passed = False

            aggregated_results.append({
                "row_index": row_index,
                "variables": row,
                "requests": run_results,
            })

        reporter = SuiteHtmlReporter(plan.name, self._get_working_dir())
        report_path = reporter.generate(aggregated_results, plan.report_path)
        ColoredOutput.info(f"Suite report generated: {report_path}")

        return all_passed

    def _apply_suite_options(self, options: Dict[str, Any]):
        if self.args.timeout is None and "timeout" in options:
            self.args.timeout = options["timeout"]
        if options.get("insecure"):
            self.args.insecure = True

    def _apply_row_variables(self, var_context: VariableContext, suite_vars: Dict[str, Any], row: Dict[str, Any]):
        """Priority (low to high): suite Vars < DataSet/CSV row < CLI --var overrides."""
        var_context.tempvars = {}
        for key, value in suite_vars.items():
            var_context.put_tempvars(str(key), str(value))
        for key, value in row.items():
            var_context.put_tempvars(str(key), '' if value is None else str(value))
        for key, value in (self.args.variables or {}).items():
            var_context.put_tempvars(str(key), str(value))

    def _run_single_request(self, source: RequestSource, index: int, total: int) -> Dict[str, Any]:
        try:
            ColoredOutput.file_processing(source.label, index, total)
            if source.file_path:
                result = self.processor.process_request(source.file_path)
            else:
                result = self.processor.process_request_text(source.raw_yaml, source.label)
            ColoredOutput.success(f"✓ Successfully processed: {source.label}")
            return result
        except FileNotFoundError as err:
            ColoredOutput.error(f"✗ File not found: {err}")
            return {"status": "error", "message": str(err), "file": source.label}
        except ValueError as err:
            ColoredOutput.error(f"✗ Validation error in {source.label}: {err}")
            return {"status": "error", "message": str(err), "file": source.label}
        except Exception as err:  # pragma: no cover - defensive logging
            ColoredOutput.error(f"✗ Error processing {source.label}: {err}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            return {"status": "error", "message": str(err), "file": source.label}

    def _request_passed(self, result: Dict[str, Any]) -> bool:
        if not isinstance(result, dict):
            return False
        if result.get("status") == "error":
            return False
        asserts = result.get("asserts") or {}
        return all(details.get("pass") for details in asserts.values())

    def _get_working_dir(self) -> Path:
        if self.args.working_dir:
            return Path(self.args.working_dir)
        return Path.cwd()
