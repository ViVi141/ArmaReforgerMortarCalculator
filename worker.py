import queue
import traceback
from calculations import (
    parse_grid,
    calculate_target_coords,
    calculate_regular_mission,
    calculate_small_barrage,
    calculate_large_barrage,
    calculate_creeping_barrage,
)

def worker_thread(task_queue, result_queue):
    """
    The main function for the worker thread.
    Continuously fetches tasks from the task_queue, processes them,
    and puts the result or an exception onto the result_queue.
    """
    while True:
        try:
            task = task_queue.get(block=True)
            if task is None:  # Sentinel value to exit the thread
                break

            result = process_task(task)
            result_queue.put(result)
        except Exception as e:
            # Pass exceptions back to the main thread to be handled
            result_queue.put(e)
        finally:
            task_queue.task_done()

def process_task(task):
    """
    Processes a single calculation task.
    """
    mission_type = task['mission_type']
    ammo = task['ammo']
    creep_direction = task['creep_direction']
    
    fo_grid_str = task['fo_grid_str']
    fo_elev = task['fo_elev']
    fo_azimuth_deg = task['fo_azimuth_deg']
    fo_dist = task['fo_dist']
    fo_elev_diff = task['fo_elev_diff']
    corr_lr = task['corr_lr']
    corr_ad = task['corr_ad']
    
    mortars_data = task['mortars']

    # Reconstruct mortar data, parsing grid strings
    mortars = []
    for m_data in mortars_data:
        coords = parse_grid(m_data['grid'])
        mortars.append({
            "coords": coords,
            "elev": m_data['elev'],
            "callsign": m_data['callsign']
        })

    # Calculate initial target coordinates
    initial_target_easting, initial_target_northing = calculate_target_coords(
        fo_grid_str, fo_azimuth_deg, fo_dist, fo_elev_diff, corr_lr, corr_ad
    )
    initial_target_elev = fo_elev + fo_elev_diff
    initial_target = (initial_target_easting, initial_target_northing, initial_target_elev)

    # Dispatch to the correct calculation function based on mission type
    if mission_type == "Regular":
        solutions = calculate_regular_mission(mortars, initial_target, ammo)
    elif mission_type == "Small Barrage":
        solutions = calculate_small_barrage(mortars, initial_target, ammo)
    elif mission_type == "Large Barrage":
        solutions = calculate_large_barrage(mortars, initial_target, ammo)
    elif mission_type == "Creeping Barrage":
        solutions = calculate_creeping_barrage(mortars, initial_target, creep_direction, ammo)
    else:
        raise ValueError(f"Invalid mission type: {mission_type}")

    return solutions