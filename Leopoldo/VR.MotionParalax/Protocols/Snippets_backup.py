### Initital Parameters

# Observer location
observer_location = (0.0, 1.5)
# Circle center
C = (1.8 , 2.38334)
# Radius at reference 1 meter
distance_ref = 1.0
r = 0.075
# Height at reference 1 meter
h = 0.37
# Occluder nearmost point
Occluder_near = (1.4, 2.30829)
#Occluder farthest point
Occluder_far = (1.4, 2.86829)


# Vector calculation between observer location and circle center ( observer_location to C)

# Step 1: Compute vector v = C - A
vx = C[0] - observer_location[0]
vz = C[1] - observer_location[1]

print("Vector v:", (vx, vz))

# Step 2: Define parametric equation
# P(t) = (Ax + vx*t, Az + vz*t)

def parametric_point(t):
    x = observer_location[0] + vx * t
    z = observer_location[1] + vz * t
    return (x, z)

# Step 3: Convert to z(x)
# t = (x - Ax) / vx

def z_from_x(x):
    t = (x - observer_location[0]) / vx
    z = observer_location[1] + vz * t
    return z

# Step 4: Test with chosen x values
x_values = [2, 2.5, 3, 4, 5]

print("\nPoints on the line:")
for x in x_values:
    z = z_from_x(x)
    print(f"x = {x:.2f} -> z = {z:.5f}")


# Height and radius scaling calculation (need to get half_height at the end)

def scale_radius_to_constant_retinal_size(size_ref, distance_ref, distance_new):
    return size_ref * (distance_new / distance_ref)


# Example usage:

# radius example
radius_ref = 0.075
d_ref = 1.0
d_new = 3.0

radius_new = scale_radius_to_constant_retinal_size(radius_ref, d_ref, d_new)
print("Scaled radius:", radius_new)

def scale_height_to_constant_retinal_size(size_ref, distance_ref, distance_new):
    return size_ref * (distance_new / distance_ref)


# Example usage:

# height example
height_ref = 0.37
d_ref = 1.0
d_new = 3.0

height_new = scale_height_to_constant_retinal_size(height_ref, d_ref, d_new)
print("Scaled height:", height_new)


# Snippet that gets tangent points and both the point of and angle of crossing with x = 0

import math

def tangent_analysis(cx, cy, r, px, py):
    # Step 1: vector from center to point
    vx = px - cx
    vy = py - cy
    
    d2 = vx*vx + vy*vy
    d = math.sqrt(d2)
    
    if d < r:
        return None  # no tangents
    
    # Step 2: base point
    lam = (r*r) / d2
    bx = cx + lam * vx
    by = cy + lam * vy
    
    # Step 3: perpendicular direction
    perp_x = -vy
    perp_y = vx
    perp_len = math.sqrt(perp_x**2 + perp_y**2)
    perp_x /= perp_len
    perp_y /= perp_len
    
    # Step 4: offset
    mu = (r / d) * math.sqrt(d2 - r*r)
    ox = mu * perp_x
    oy = mu * perp_y
    
    # Tangent points
    t1 = (bx + ox, by + oy)
    t2 = (bx - ox, by - oy)
    
    results = []
    
    for (tx, ty) in [t1, t2]:
        # slope of line from tangent point to P
        m = (py - ty) / (px - tx)
        
        # intersection with x = 0 (y-intercept)
        y_intercept = ty - m * tx
        
        # angle with vertical (x = 0)
        angle_vertical = math.degrees(math.atan(1 / abs(m)))
        
        results.append({
            "tangent_point": (tx, ty),
            "slope": m,
            "intersection_x0": (0, y_intercept),
            "angle_with_x0_deg": angle_vertical
        })
    
    return results