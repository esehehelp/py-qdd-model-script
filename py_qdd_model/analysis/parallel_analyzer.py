import numpy as np
import os
import multiprocessing
from typing import Dict, List

from ..schema import MotorParams
from ..models.motor_model import MotorModel


def analyze_chunk(params: MotorParams, i_chunk: np.ndarray, rpm_chunk: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Worker function executed in a separate process to analyze a chunk of the grid.
    This function must be at the top level of the module for multiprocessing to work.
    """
    model = MotorModel(params)
    return model.analyze(i_chunk, rpm_chunk)

def run_parallel_analysis(params: MotorParams, current_range: np.ndarray, rpm_range: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Runs the motor analysis in parallel by splitting the calculation grid into chunks
    and processing them on different CPU cores.
    """
    # Create the full meshgrid
    I, RPM = np.meshgrid(current_range, rpm_range)

    # Determine the number of processes to use (e.g., number of CPU cores)
    try:
        n_procs = os.cpu_count() or 1
    except NotImplementedError:
        n_procs = 1

    # Split the RPM and I arrays into chunks for each process
    # We split along the RPM axis (axis=0)
    rpm_chunks = np.array_split(RPM, n_procs, axis=0)
    i_chunks = np.array_split(I, n_procs, axis=0)

    # Create a list of tasks for the process pool
    tasks = [(params, i_chunks[i], rpm_chunks[i]) for i in range(n_procs)]

    # Use a multiprocessing pool to execute the tasks in parallel
    with multiprocessing.Pool(processes=n_procs) as pool:
        chunk_results: List[Dict[str, np.ndarray]] = pool.starmap(analyze_chunk, tasks)

    # Stitch the results from all chunks back together
    if not chunk_results:
        return {}

    # Get the keys from the first result dictionary
    final_result: Dict[str, np.ndarray] = {}
    keys = chunk_results[0].keys()

    for key in keys:
        # Concatenate the arrays for this key from all chunk results
        arrays_to_stitch = [res[key] for res in chunk_results]
        final_result[key] = np.concatenate(arrays_to_stitch, axis=0)

    return final_result
