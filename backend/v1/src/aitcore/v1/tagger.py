"""
Tagger CLI - Command-line interface for the AI Code Tagging system.

This module provides a CLI entry point for running the tagger service
as a standalone application or within a Docker container.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .config import init_config, get_config
from .utils import setup_logger, get_logger
from .workflow import (
    WorkflowOrchestrator,
    TechSpecGenerationStep,
    TaggingSuggestionStep,
    TaggingApplicationStep,
    RollbackStep,
)


def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Set up the CLI argument parser.
    
    Returns:
        ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="AI Code Tagging System - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TechSpec from Figma/Excel
  python -m aitcore.v1.tagger generate-spec --techspec /path/to/spec.xlsx

  # Suggest tagging locations
  python -m aitcore.v1.tagger suggest-tagging --repo /path/to/repo --spec /path/to/spec.xlsx

  # Apply tagging suggestions
  python -m aitcore.v1.tagger apply-tagging --repo /path/to/repo --suggestions /path/to/suggestions.json

  # Run full workflow
  python -m aitcore.v1.tagger run-workflow --repo /path/to/repo --spec /path/to/spec.xlsx
        """
    )
    
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8880,
        help="Port for service (if applicable)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for results"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # generate-spec subcommand
    gen_spec = subparsers.add_parser(
        "generate-spec",
        help="Generate TechSpec from Figma capture or Excel file"
    )
    gen_spec.add_argument(
        "--techspec",
        type=Path,
        required=True,
        help="Path to TechSpec Excel file"
    )
    gen_spec.add_argument(
        "--figma-file",
        type=Path,
        help="Path to Figma capture file"
    )
    
    # suggest-tagging subcommand
    suggest = subparsers.add_parser(
        "suggest-tagging",
        help="Generate tagging suggestions for code locations"
    )
    suggest.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Path to repository root"
    )
    suggest.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to TechSpec file"
    )
    suggest.add_argument(
        "--branch",
        default="main",
        help="Repository branch (default: main)"
    )
    
    # apply-tagging subcommand
    apply = subparsers.add_parser(
        "apply-tagging",
        help="Apply tagging suggestions to repository files"
    )
    apply.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Path to repository root"
    )
    apply.add_argument(
        "--suggestions",
        type=Path,
        required=True,
        help="Path to suggestions JSON file"
    )
    apply.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )
    
    # run-workflow subcommand
    workflow = subparsers.add_parser(
        "run-workflow",
        help="Run complete tagging workflow"
    )
    workflow.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Path to repository root"
    )
    workflow.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to TechSpec file"
    )
    workflow.add_argument(
        "--branch",
        default="main",
        help="Repository branch (default: main)"
    )
    workflow.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )
    
    # serve subcommand (for API server)
    serve = subparsers.add_parser(
        "serve",
        help="Start API server"
    )
    serve.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    serve.add_argument(
        "--port",
        type=int,
        default=8880,
        help="Server port (default: 8880)"
    )
    
    return parser


def run_generate_spec(args, logger: logging.Logger, config) -> int:
    """Run TechSpec generation."""
    logger.info(f"Generating TechSpec from {args.techspec}")
    
    try:
        orchestrator = WorkflowOrchestrator(f"spec_{id(args)}")
        orchestrator.add_step(TechSpecGenerationStep())
        
        input_data = {
            "techspec_path": str(args.techspec),
            "figma_file": str(args.figma_file) if args.figma_file else None,
            "output_dir": str(args.output_dir or config.outputs_dir),
        }
        
        result = orchestrator.execute(input_data)
        
        if result.success:
            logger.info("TechSpec generation completed successfully")
            return 0
        else:
            logger.error("TechSpec generation failed")
            return 1
    
    except Exception as e:
        logger.error(f"TechSpec generation error: {e}", exc_info=True)
        return 1


def run_suggest_tagging(args, logger: logging.Logger, config) -> int:
    """Run tagging suggestion generation."""
    logger.info(f"Generating tagging suggestions for {args.repo}")
    
    try:
        orchestrator = WorkflowOrchestrator(f"suggest_{id(args)}")
        orchestrator.add_step(TaggingSuggestionStep())
        
        input_data = {
            "repo_path": str(args.repo),
            "techspec_path": str(args.spec),
            "branch": args.branch,
            "output_dir": str(args.output_dir or config.outputs_dir),
        }
        
        result = orchestrator.execute(input_data)
        
        if result.success:
            logger.info("Tagging suggestion generation completed successfully")
            return 0
        else:
            logger.error("Tagging suggestion generation failed")
            return 1
    
    except Exception as e:
        logger.error(f"Tagging suggestion error: {e}", exc_info=True)
        return 1


def run_apply_tagging(args, logger: logging.Logger, config) -> int:
    """Run tagging application."""
    logger.info(f"Applying tagging suggestions to {args.repo}")
    
    try:
        orchestrator = WorkflowOrchestrator(f"apply_{id(args)}")
        orchestrator.add_step(TaggingApplicationStep())
        
        input_data = {
            "repo_path": str(args.repo),
            "suggestions_path": str(args.suggestions),
            "dry_run": args.dry_run,
            "output_dir": str(args.output_dir or config.outputs_dir),
        }
        
        result = orchestrator.execute(input_data)
        
        if result.success:
            logger.info("Tagging application completed successfully")
            return 0
        else:
            logger.error("Tagging application failed")
            return 1
    
    except Exception as e:
        logger.error(f"Tagging application error: {e}", exc_info=True)
        return 1


def run_workflow(args, logger: logging.Logger, config) -> int:
    """Run complete tagging workflow."""
    logger.info(f"Running complete workflow for {args.repo}")
    
    try:
        orchestrator = WorkflowOrchestrator(f"workflow_{id(args)}")
        orchestrator.add_step(TechSpecGenerationStep())
        orchestrator.add_step(TaggingSuggestionStep())
        orchestrator.add_step(TaggingApplicationStep())
        
        input_data = {
            "repo_path": str(args.repo),
            "techspec_path": str(args.spec),
            "branch": args.branch,
            "dry_run": args.dry_run,
            "output_dir": str(args.output_dir or config.outputs_dir),
        }
        
        result = orchestrator.execute(input_data)
        
        if result.success:
            logger.info("Complete workflow completed successfully")
            return 0
        else:
            logger.error("Complete workflow failed")
            return 1
    
    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        return 1


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    parser = setup_cli_parser()
    args = parser.parse_args(argv)
    
    # Initialize configuration
    config = init_config()
    
    # Setup logging
    logger = setup_logger(
        "aitcore.tagger",
        log_level=args.loglevel,
        log_dir=str(config.logs_dir),
        log_file="tagger.log"
    )
    
    logger.info("=" * 80)
    logger.info("AI Code Tagging System - Tagger CLI")
    logger.info("=" * 80)
    logger.info(f"Configuration: {config.to_dict()}")
    
    # Route to appropriate command handler
    if args.command == "generate-spec":
        return run_generate_spec(args, logger, config)
    elif args.command == "suggest-tagging":
        return run_suggest_tagging(args, logger, config)
    elif args.command == "apply-tagging":
        return run_apply_tagging(args, logger, config)
    elif args.command == "run-workflow":
        return run_workflow(args, logger, config)
    elif args.command == "serve":
        # For serve command, we import and run the API router
        logger.info(f"Starting API server on {args.host}:{args.port}")
        try:
            import uvicorn
            from aitapi.v1.router import app
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level=args.loglevel.lower()
            )
            return 0
        except ImportError:
            logger.error("uvicorn not installed. Install with: pip install uvicorn")
            return 1
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            return 1
    else:
        # No command provided - print help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
