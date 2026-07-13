"""
phase2.validation.logger
========================

Provides isolated and specialized logging for the Validation Suite.
Ensures validation execution details are printed without modifying or 
interfering with the core `LoggingService` of Phase 2.
"""

import logging
import sys
from pathlib import Path


class ValidationLogger:
    """
    Dedicated logger factory for validation tests.
    Logs standard events to the console and detailed execution flow to a file.
    """
    
    @staticmethod
    def get_logger(name: str = "ValidationSuite") -> logging.Logger:
        logger = logging.getLogger(name)
        
        # Prevent duplicate handlers if already configured
        if logger.hasHandlers():
            return logger
            
        logger.setLevel(logging.INFO)
        # We enforce no propagation to avoid duplicate logs in the main Phase 2 logger
        logger.propagate = False
        
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | VALIDATION | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. File Handler
        try:
            log_dir = Path("phase2/validation/reports/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_dir / "validation_run.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup text file handler for validation: {e}")
            
        return logger

# Convenience singleton instance for direct import usage if needed within tests
logger = ValidationLogger.get_logger()
