# File: smurfs/smurfs_ui/process_manager.py
import multiprocessing as mp
from typing import Dict, Any
import traceback
from queue import Empty

from smurfs.smurfs_common.support.logging import ProcessLogger
from smurfs.smurfs_common.support.mprint import MPrinter, mprint, error, state

class ProcessManagerObjects:
    process_logger : ProcessLogger | None = None


def run_analysis_process(value_dict: Dict[str, Any], log_queue: mp.Queue):
    ProcessManagerObjects.process_logger = ProcessLogger(log_queue)
    try:
        # Initialize the process logger
        MPrinter.initialize(ProcessManagerObjects.process_logger)

        # Import here to avoid circular imports
        from smurfs.smurfs_ui.smurfs_helper import (
            validate_smurfs_inputs, create_smurfs_instance, run_smurfs_analysis
        )

        # Run validation
        is_valid, error_msg = validate_smurfs_inputs(value_dict)
        if not is_valid:
            ProcessManagerObjects.process_logger.log_error(f"Validation Error: {error_msg}")
            return False

        # Create and run SMURFS
        smurfs = create_smurfs_instance(value_dict)
        run_smurfs_analysis(smurfs, value_dict)

        ProcessManagerObjects.process_logger.log("Analysis completed successfully", "INFO")
        return True

    except Exception as e:
        tb = traceback.format_exc()
        ProcessManagerObjects.process_logger.log_error(f"Error occurred during analysis: {str(e)}")
        ProcessManagerObjects.process_logger.log_error(tb)

        print(f"Error occurred during analysis: {str(e)}")
        print(tb)
        return False