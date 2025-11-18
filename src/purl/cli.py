"""
Command-line interface for purl
"""

import sys

from .processor import RequestProcessor
from .args import parse_arguments
from .output import ColoredOutput
from .init import initialize_project


def main():
    """Main entry point for CLI"""
    # Parse arguments
    args = parse_arguments()
    
    # Handle --init flag
    if args.init:
        try:
            initialize_project(configs=args.init_configs)
            return 0
        except Exception as e:
            ColoredOutput.error(f"Failed to initialize project: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # Validate that request files are provided
    if not args.request_files:
        ColoredOutput.error("No request files specified")
        return 1
    
    # Track success/failure
    total_files = len(args.request_files)
    successful = 0
    failed = 0
    
    try:
        # Create and initialize processor (gets config from args singleton)
        processor = RequestProcessor()
        processor.initialize()
        
        # Show config if specified
        if args.config_names:
            ColoredOutput.env_config(args.config_names)
        
        # Process each request file
        for index, request_file in enumerate(args.request_files, start=1):
            try:
                # Show which file we're processing
                ColoredOutput.file_processing(request_file, index, total_files)
                
                # Process request: read -> resolve -> read
                status = processor.process_request(request_file)
    
                # Success
                successful += 1
                ColoredOutput.success(f"✓ Successfully processed: {request_file}")
                
            except FileNotFoundError as e:
                failed += 1
                ColoredOutput.error(f"✗ File not found: {e}")
                if total_files == 1:
                    return 1
                    
            except ValueError as e:
                failed += 1
                ColoredOutput.error(f"✗ Validation error in {request_file}: {e}")
                if total_files == 1:
                    return 1
                    
            except Exception as e:
                failed += 1
                ColoredOutput.error(f"✗ Error processing {request_file}: {e}")
                if args.debug:
                    import traceback
                    traceback.print_exc()
                    return 1
        
        # Summary for multiple files
        if total_files > 1:
            ColoredOutput.separator("=", 80, 'cyan')
            ColoredOutput.header("SUMMARY")
            ColoredOutput.separator("=", 80, 'cyan')
            ColoredOutput.key_value("Total files", str(total_files))
            ColoredOutput.key_value("Successful", str(successful))
            if failed > 0:
                ColoredOutput.key_value("Failed", str(failed))
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        ColoredOutput.warning("Interrupted by user")
        return 130
    except Exception as e:
        ColoredOutput.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
