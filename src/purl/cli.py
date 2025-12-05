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


def main():
    """Main entry point for CLI."""
    args = parse_arguments()
    if _handle_init_request(args):
        return 0 if not getattr(args, 'init_failed', False) else 1

    # Initialize app (create folders/files)
    AppManager().initialize()
    # Load variables
    VariableContext().load()

    try:
        if args.suite_file:
            runner = SuiteRunner()
        else:
            runner = RequestRunner()

        runner.run()
        return 0
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
