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

def worker_thread(task_queue, result_queue, app):
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
            # Print the full traceback to the console for debugging
            traceback.print_exc()
            # Pass exceptions back to the main thread to be handled
            result_queue.put(e)
        finally:
            # Always generate the event, even if an exception occurred
            app.event_generate("<<CalculationFinished>>")
            task_queue.task_done()

def process_task(task):
    """
    Processes a single calculation task.
    """
    mission_type = task['mission_type']
    targeting_mode = task['targeting_mode']
    faction = task['faction']
    ammo = task['ammo']
    creep_direction = task['creep_direction']
    creep_spread = task['creep_spread']
    
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
    if targeting_mode == "Polar":
        initial_target_easting, initial_target_northing = calculate_target_coords(
            fo_grid_str, fo_azimuth_deg, fo_dist, fo_elev_diff, corr_lr, corr_ad
        )
        initial_target_elev = fo_elev + fo_elev_diff
        initial_target = (initial_target_easting, initial_target_northing, initial_target_elev)
    else: # Grid
        # In Grid mode, the target coordinates are taken directly from the UI
        # We need to get them from the task dictionary
        target_grid_str = task['target_grid_str']
        target_elev = task['target_elev']
        target_easting, target_northing = parse_grid(target_grid_str)
        initial_target = (target_easting, target_northing, target_elev)

    # Dispatch to the correct calculation function based on mission type
    if mission_type == "Regular":
        solutions = calculate_regular_mission(mortars, initial_target, faction, ammo)
    elif mission_type == "Small Barrage":
        solutions = calculate_small_barrage(mortars, initial_target, faction, ammo)
    elif mission_type == "Large Barrage":
        solutions = calculate_large_barrage(mortars, initial_target, faction, ammo)
    elif mission_type == "Creeping Barrage":
        solutions = calculate_creeping_barrage(mortars, initial_target, creep_direction, faction, ammo, creep_spread)
    else:
        raise ValueError(f"Invalid mission type: {mission_type}")

    return solutions