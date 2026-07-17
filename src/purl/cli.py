"""Command-line interface for purl."""

import sys

from .request_runner import RequestRunner
from .suite_runner import SuiteRunner
from .args import parse_arguments, PurlArgs
from .output import ColoredOutput
from .init import initialize_project
from .app_manager import AppManager
from .variables import VariableContext

def _handle_init_request(args) -> bool:
    """Run project initialization if requested. Returns True if program should exit."""
    if not args.init:
        return False
    try:
        initialize_project(configs=args.init_configs)
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        ColoredOutput.error(f"Failed to initialize project: {exc}")
        import traceback
        traceback.print_exc()
        return True


def _requests_passed(results) -> bool:
    """Determine overall pass/fail from a plain (non-suite) RequestRunner.run() result."""
    if isinstance(results, tuple):  # early-return error case (e.g. no request files)
        return False
    if not isinstance(results, list):
        return True
    for result in results:
        if not isinstance(result, dict):
            continue
        if result.get("status") == "error":
            return False
        asserts = result.get("asserts") or {}
        if not all(details.get("pass") for details in asserts.values()):
            return False
    return True


def _use_utf8_console():
    """Some Windows consoles default stdout/stderr to a legacy codepage (e.g. cp1252),
    which raises UnicodeEncodeError on the checkmarks/symbols used in console output."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass


def main():
    """Main entry point for CLI."""
    _use_utf8_console()
    args = parse_arguments()
    if _handle_init_request(args):
        return 0 if not getattr(args, 'init_failed', False) else 1

    # Initialize app (create folders/files)
    AppManager().initialize()
    # Load variables
    VariableContext().load()

    try:
        if args.suite_file:
            success = SuiteRunner().run()
        else:
            success = _requests_passed(RequestRunner().run())

        return 0 if success else 1
    except KeyboardInterrupt:
        ColoredOutput.warning("Interrupted by user")
        return 130
    except Exception as exc:  # pragma: no cover - defensive logging
        ColoredOutput.error(f"Unexpected error: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
