"""Utility for executing request files via CLI arguments."""

import re
from .request_processor import RequestProcessor
from .args import PurlArgs
from .output import ColoredOutput


class RequestRunner:
    """Executes request files defined in CLI arguments."""

    def __init__(self):
        self.args = PurlArgs()
        self.processor = RequestProcessor()
        self.successful = 0
        self.failed = 0
        self.total_files = 0
        self._current_file = ""
        self._current_index = 0

    def run(self):
        """Initialize processor and execute all request files."""
        if not self.args.request_files:
            ColoredOutput.error("No request files specified")
            return 0, 1

        self.processor.initialize()

        if self.args.config_names:
            ColoredOutput.env_config(self.args.config_names)

        self.total_files = len(self.args.request_files)
        return self._run_requests()

    def _process_single_request(self):
        """Execute a single request file with error handling."""
        try:
            ColoredOutput.file_processing(self._current_file, self._current_index, self.total_files)
            result = self.processor.process_request(self._current_file)
            ColoredOutput.success(f"✓ Successfully processed: {self._current_file}")
            return result
        except FileNotFoundError as err:
            ColoredOutput.error(f"✗ File not found: {err}")
            return {
                'status' : 'error',
                'message' : err,
                'file' : self._current_file
            }
        except ValueError as err:
            ColoredOutput.error(f"✗ Validation error in {self._current_file}: {err}")
            return {
                'status' : 'error',
                'message' : err,
                'file' : self._current_file
            }
        except Exception as err:  # pragma: no cover - defensive logging
            ColoredOutput.error(f"✗ Error processing {self._current_file}: {err}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            return {
                'status' : 'error',
                'message' : err,
                'file' : self._current_file
            }

    def _run_requests(self):
        """Iterate through all request files and summarize results."""
        results = []
        for index, request_file in enumerate(self.args.request_files, start=1):
            self._current_index = index
            self._current_file = request_file
            results.append(self._process_single_request())
        return results
