import queue
import traceback
import math # Import math for calculations
from ballistics import MILS_PER_REVOLUTION # Import MILS_PER_REVOLUTION
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
        task = task_queue.get(block=True)
        if task is None:  # Sentinel value to exit the thread
            break

        try:
            result = process_task(task)
            result_queue.put(result)
        except Exception as e:
            # Catch specific ValueErrors from calculations and return a structured error
            if isinstance(e, ValueError) and "No valid solution" in str(e):
                result_queue.put({
                    'is_trp_list_calc': task.get('is_trp_list_calc', False),
                    'trp_name': task.get('trp_name', 'Unknown TRP'),
                    'solutions': [],
                    'error': str(e)
                })
            else:
                # For other unexpected exceptions, print traceback and pass the exception
                traceback.print_exc()
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
        # Ensure target_elev is a float, defaulting to 0.0 if it's an empty string or invalid
        target_elev = float(task['target_elev']) if isinstance(task['target_elev'], str) and task['target_elev'].strip() != "" else (task['target_elev'] if isinstance(task['target_elev'], (int, float)) else 0.0)
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

    # Process solutions to add azimuth, distance, and elev_diff
    processed_solutions = []
    for sol in solutions:
        mortar_e, mortar_n = sol['mortar']['coords']
        target_e, target_n, target_elev = sol['target_coords']
        
        delta_easting, delta_northing = target_e - mortar_e, target_n - mortar_n
        mortar_target_dist = math.sqrt(delta_easting**2 + delta_northing**2)
        mortar_target_elev_diff = target_elev - sol['mortar']['elev']
        azimuth_rad_mt = math.atan2(delta_easting, delta_northing)
        
        # Get faction from task, default to NATO if not present
        selected_faction = task.get('faction', 'NATO')
        mils_in_revolution = MILS_PER_REVOLUTION.get(selected_faction, 6400)
        azimuth_mils_mt = (azimuth_rad_mt / math.pi) * (mils_in_revolution / 2)
        if azimuth_mils_mt < 0:
            azimuth_mils_mt += mils_in_revolution
        
        sol['azimuth'] = azimuth_mils_mt
        sol['distance'] = mortar_target_dist
        sol['elev_diff'] = mortar_target_elev_diff
        sol['target_elev'] = target_elev # Add target_elev to the solution dictionary
        processed_solutions.append(sol)

    # Always return a dictionary with the necessary flags
    return {
        'is_trp_list_calc': task.get('is_trp_list_calc', False),
        'trp_name': task.get('trp_name', None),
        'original_trp_grid': task.get('target_grid_str', None), # Add original TRP grid
        'original_trp_elev': task.get('target_elev', None), # Add original TRP elevation
        'solutions': processed_solutions
    }