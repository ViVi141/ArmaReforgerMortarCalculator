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
    # 1. Calculate the initial target position before corrections
    fo_easting, fo_northing = parse_grid(fo_grid_str, digits=10)
    azimuth_rad = math.radians(fo_azimuth_deg)
    
    initial_target_easting = fo_easting + fo_dist * math.sin(azimuth_rad)
    initial_target_northing = fo_northing + fo_dist * math.cos(azimuth_rad)

    # If there are no corrections, return the initial target position
    if corr_lr == 0 and corr_add_drop == 0:
        return initial_target_easting, initial_target_northing

    # 2. Calculate the correction vectors relative to the FO's line of sight
    # The "Add/Drop" vector is along the line of sight (azimuth_rad)
    add_drop_easting = corr_add_drop * math.sin(azimuth_rad)
    add_drop_northing = corr_add_drop * math.cos(azimuth_rad)

    # The "Left/Right" vector is perpendicular to the line of sight (+90 degrees)
    # A positive corr_lr means "Right", a negative one means "Left"
    lr_azimuth_rad = azimuth_rad + (math.pi / 2)
    lr_easting = corr_lr * math.sin(lr_azimuth_rad)
    lr_northing = corr_lr * math.cos(lr_azimuth_rad)

    # 3. Apply the correction vectors to the initial target position
    final_target_easting = initial_target_easting + add_drop_easting + lr_easting
    final_target_northing = initial_target_northing + add_drop_northing + lr_northing
    
    return final_target_easting, final_target_northing

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

def check_mortar_fo_axis(mortar_coords, fo_coords, target_coords):
    """
    Checks if the target is between the mortar and the FO.
    Returns True if target is between mortar and FO, False otherwise.
    """
    # Vector from mortar to FO
    v_mf = (fo_coords[0] - mortar_coords[0], fo_coords[1] - mortar_coords[1])
    # Vector from mortar to Target
    v_mt = (target_coords[0] - mortar_coords[0], target_coords[1] - mortar_coords[1])

    # Dot product of the two vectors
    dot_product = v_mf[0] * v_mt[0] + v_mf[1] * v_mt[1]
    
    # Squared length of the mortar-FO vector
    len_sq_mf = v_mf[0]**2 + v_mf[1]**2

    # If the dot product is between 0 and the squared length of the mortar-FO vector,
    # the projection of the target onto the mortar-FO line is between the mortar and the FO.
    if 0 < dot_product < len_sq_mf:
        # Check for collinearity
        cross_product = v_mf[0] * v_mt[1] - v_mf[1] * v_mt[0]
        if abs(cross_product) < 1e-6: # Using a small epsilon for floating point comparison
             return True
    return False


def check_danger_close(fo_coords, target_coords, dispersion):
    """
    Checks if the target's dispersion radius is dangerously close to the FO.
    Returns True if danger close, False otherwise.
    """
    distance_sq = (target_coords[0] - fo_coords[0])**2 + (target_coords[1] - fo_coords[1])**2
    return distance_sq <= (dispersion + 100)**2

def check_unreliable_correction(mortar_coords, fo_coords, target_coords):
    """
    Checks if the target is on the same axis as the mortar and FO, which can lead to unreliable corrections.
    Returns True if the correction is unreliable, False otherwise.
    """
    v_mf = (fo_coords[0] - mortar_coords[0], fo_coords[1] - mortar_coords[1])
    v_mt = (target_coords[0] - mortar_coords[0], target_coords[1] - mortar_coords[1])
    
    mag_mf = math.sqrt(v_mf[0]**2 + v_mf[1]**2)
    mag_mt = math.sqrt(v_mt[0]**2 + v_mt[1]**2)
    
    if mag_mf > 0 and mag_mt > 0:
        dot_product = v_mf[0]*v_mt[0] + v_mf[1]*v_mt[1]
        cos_theta = dot_product / (mag_mf * mag_mt)
        if abs(cos_theta) > 0.99:
            return True
    return False