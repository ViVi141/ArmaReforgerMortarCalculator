import math
from ballistics import BALLISTIC_DATA

def interpolate(x, x1, y1, x2, y2):
    """Helper function for linear interpolation."""
    if x2 == x1:
        return y1
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def parse_grid(grid_str, digits=10):
    """Parses an 8 or 10 digit grid string into easting and northing."""
    grid_str = grid_str.replace(" ", "")
    half = len(grid_str) // 2
    if len(grid_str) != digits:
        raise ValueError(f"Grid must be {digits} digits")
    
    if digits == 8:
        easting = int(grid_str[:half]) * 10
        northing = int(grid_str[half:]) * 10
    elif digits == 10:
        easting = int(grid_str[:half])
        northing = int(grid_str[half:])
    else:
        raise ValueError("Grid must be 8 or 10 digits")
        
    return easting, northing

def calculate_target_coords(fo_grid_str, fo_azimuth_deg, fo_dist, fo_elev_diff, corr_lr, corr_add_drop):
    """
    Calculates the target's coordinates based on FO data and corrections.
    This version uses vector addition for a more accurate calculation.
    """
    fo_easting, fo_northing = parse_grid(fo_grid_str, digits=10)
    azimuth_rad = math.radians(fo_azimuth_deg)
    
    initial_target_easting = fo_easting + fo_dist * math.sin(azimuth_rad)
    initial_target_northing = fo_northing + fo_dist * math.cos(azimuth_rad)

    if corr_lr == 0 and corr_add_drop == 0:
        return initial_target_easting, initial_target_northing

    # Let the new function determine the best correction
    return calculate_best_correction(initial_target_easting, initial_target_northing, azimuth_rad, corr_lr, corr_add_drop)

def calculate_best_correction(initial_e, initial_n, fo_azimuth_rad, lr_corr, ad_corr):
    """
    Calculates the four possible correction points and returns the one
    closest to the original uncorrected target location.
    """
    possible_corrections = [
        (lr_corr, ad_corr),
        (-lr_corr, ad_corr),
        (lr_corr, -ad_corr),
        (-lr_corr, -ad_corr)
    ]

    best_point = None
    min_dist_sq = float('inf')

    for lr, ad in possible_corrections:
        # Calculate the correction vectors
        ad_e = ad * math.sin(fo_azimuth_rad)
        ad_n = ad * math.cos(fo_azimuth_rad)
        
        lr_azimuth = fo_azimuth_rad + (math.pi / 2)
        lr_e = lr * math.sin(lr_azimuth)
        lr_n = lr * math.cos(lr_azimuth)

        # Apply correction
        corrected_e = initial_e + ad_e + lr_e
        corrected_n = initial_n + ad_n + lr_n

        # Check distance from the *original* point
        dist_sq = (corrected_e - initial_e)**2 + (corrected_n - initial_n)**2
        
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_point = (corrected_e, corrected_n)
            
    return best_point

def find_valid_solutions(ammo, distance, elev_diff):
    """Finds all valid firing solutions for a given ammo, distance, and elevation change."""
    valid_solutions = []
    for charge, charge_data in BALLISTIC_DATA[ammo].items():
        charge_ranges = charge_data['ranges']
        sorted_ranges = sorted(charge_ranges.keys())
        if not (sorted_ranges[0] <= distance <= sorted_ranges[-1]):
            continue

        for i in range(len(sorted_ranges) - 1):
            if sorted_ranges[i] <= distance <= sorted_ranges[i+1]:
                r1, r2 = sorted_ranges[i], sorted_ranges[i+1]
                d1, d2 = charge_ranges[r1], charge_ranges[r2]
                
                base_elev = interpolate(distance, r1, d1["elev"], r2, d2["elev"])
                base_tof = interpolate(distance, r1, d1["tof"], r2, d2["tof"])
                base_delev = interpolate(distance, r1, d1["delev"], r2, d2["delev"])
                
                elevation_correction = (elev_diff / 100) * base_delev
                final_elevation = base_elev + elevation_correction
                
                valid_solutions.append({
                    "charge": charge,
                    "elev": final_elevation,
                    "tof": base_tof,
                    "dispersion": charge_data['dispersion']
                })
                break
    return valid_solutions

def check_target_on_mortar_fo_axis(mortar_coords, fo_coords, target_coords, lane_width=100):
    """
    Checks if the target is within a 'lane' between the mortar and the FO,
    which can lead to unreliable corrections.
    Returns True if the correction is unreliable, False otherwise.
    """
    # Vectors
    v_mf = (fo_coords[0] - mortar_coords[0], fo_coords[1] - mortar_coords[1]) # Mortar to FO
    v_mt = (target_coords[0] - mortar_coords[0], target_coords[1] - mortar_coords[1]) # Mortar to Target

    len_sq_mf = v_mf[0]**2 + v_mf[1]**2
    if len_sq_mf == 0:
        return False # Mortar and FO are at the same spot, no axis to be on

    # 1. Check if the projection of the target lies on the segment between mortar and FO
    dot_product = v_mf[0] * v_mt[0] + v_mf[1] * v_mt[1]
    if not (0 < dot_product < len_sq_mf):
        return False

    # 2. Check if the target is close to the line (within the lane)
    # Perpendicular distance from target to the line defined by mortar-FO
    cross_product = abs(v_mf[0] * v_mt[1] - v_mf[1] * v_mt[0])
    distance_from_line = cross_product / math.sqrt(len_sq_mf)
    
    return distance_from_line < (lane_width / 2)

def check_danger_close(fo_coords, target_coords, dispersion):
    """
    Checks if the target's dispersion radius is dangerously close to the FO.
    Returns True if danger close, False otherwise.
    """
    distance_sq = (target_coords[0] - fo_coords[0])**2 + (target_coords[1] - fo_coords[1])**2
    return distance_sq <= (dispersion + 100)**2

def calculate_new_fo_data(fo_coords, target_coords):
    """
    Calculates the new azimuth and distance from the FO to the corrected target.
    """
    delta_easting = target_coords[0] - fo_coords[0]
    delta_northing = target_coords[1] - fo_coords[1]

    new_dist = math.sqrt(delta_easting**2 + delta_northing**2)
    new_azimuth_rad = math.atan2(delta_easting, delta_northing)
    new_azimuth_deg = math.degrees(new_azimuth_rad)
    if new_azimuth_deg < 0:
        new_azimuth_deg += 360

    return new_azimuth_deg, new_dist