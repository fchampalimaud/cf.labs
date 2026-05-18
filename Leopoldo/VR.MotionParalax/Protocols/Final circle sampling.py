# Test with the angles of the final script - angles working

import math
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

### Initial Parameters
# Edit values in this section only. Everything below uses these parameters.
PARAMS = {
    "observer_location": (0.0, 1.5),
    "circle_center": (2.2, 2.57963777777778),
    "distance_ref": 1.0,
    "radius_ref": 0.075,
    "height_ref": 0.37,
    "occluder_near": (1.4, 2.30829),
    "occluder_far": (1.4, 2.86829),
    "x_samples": [2.2, 2.3, 2.4, 2.41, 2.42, 2.43, 2.44, 2.45, 2.46, 2.47, 2.48, 2.49, 2.5, 2.544912, 2.6, 2.7, 2.8, 2.9, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    "excel_output_path": "motion_parallax_results.xlsx",
}


def observer_to_circle_vector(observer_location, circle_center):
    vx = circle_center[0] - observer_location[0]
    vz = circle_center[1] - observer_location[1]
    return vx, vz


def point_on_observer_circle_line(observer_location, circle_center, t):
    vx, vz = observer_to_circle_vector(observer_location, circle_center)
    x = observer_location[0] + vx * t
    z = observer_location[1] + vz * t
    return x, z


def z_on_observer_circle_line_at_x(observer_location, circle_center, x):
    vx, vz = observer_to_circle_vector(observer_location, circle_center)
    if vx == 0:
        raise ValueError("Cannot compute z(x): line is vertical in x.")
    t = (x - observer_location[0]) / vx
    z = observer_location[1] + vz * t
    return z


def scale_size_to_constant_retinal_size(size_ref, distance_ref, distance_new):
    if distance_ref == 0:
        raise ValueError("distance_ref cannot be zero.")
    return size_ref * (distance_new / distance_ref)


def tangent_points_from_circle_and_point(circle_center, radius, point):
    cx, cy = circle_center
    px, py = point

    vx = px - cx
    vy = py - cy

    d2 = vx * vx + vy * vy
    d = math.sqrt(d2)

    if d < radius:
        return None

    lam = (radius * radius) / d2
    bx = cx + lam * vx
    by = cy + lam * vy

    perp_x = -vy
    perp_y = vx
    perp_len = math.sqrt(perp_x * perp_x + perp_y * perp_y)
    perp_x /= perp_len
    perp_y /= perp_len

    mu = (radius / d) * math.sqrt(d2 - radius * radius)
    ox = mu * perp_x
    oy = mu * perp_y

    t1 = (bx + ox, by + oy)
    t2 = (bx - ox, by - oy)
    return [t1, t2]


def select_tangent_point_with_highest_z(tangent_points):
    return max(tangent_points, key=lambda point: point[1])


def line_analysis(point_a, point_b):
    ax, ay = point_a
    bx, by = point_b

    dx = bx - ax   # lateral
    dy = by - ay   # forward

    # --- slope & intercept (keep your original logic) ---
    if dx == 0:
        slope = math.inf
        y_intercept = None
    else:
        slope = dy / dx
        y_intercept = ay - slope * ax

    # --- angle with forward (dy axis) ---
    # signed: right = +, left = -
    angle_forward = 180 - abs(math.degrees(math.atan2(dx, dy)))

    # --- angle with vertical (x = 0) ---
    # always positive [0, 90]
    angle_vertical = math.degrees(math.atan2(abs(dx), abs(dy)))

    return {
        "line_points": (point_a, point_b),
        "slope": slope,
        "intersection_x0": (0, y_intercept) if y_intercept is not None else None,
        "angle_with_x0_deg": angle_vertical,
        "angle_with_forward_deg": angle_forward,
    }


def build_results_table(params):
    observer_location = params["observer_location"]
    base_circle_center = params["circle_center"]
    occluder_far = params["occluder_far"]
    distance_ref = params["distance_ref"]
    radius_ref = params["radius_ref"]
    height_ref = params["height_ref"]
    x_samples = params["x_samples"]

    rows = []

    for circle_center_x in x_samples:
        circle_center_z = z_on_observer_circle_line_at_x(
            observer_location,
            base_circle_center,
            circle_center_x,
        )
        current_circle_center = (circle_center_x, circle_center_z)

        scaled_radius = scale_size_to_constant_retinal_size(
            radius_ref,
            distance_ref,
            circle_center_x,
        )
        scaled_height = scale_size_to_constant_retinal_size(
            height_ref,
            distance_ref,
            circle_center_x,
        )
        scaled_half_height = scaled_height / 2.0

        tangent_points = tangent_points_from_circle_and_point(
            current_circle_center,
            scaled_radius,
            occluder_far,
        )

        if tangent_points is None:
            selected_tangent_point = None
            intersection_x0_z = None
            angle_with_x0_deg = None
            angle_with_forward_deg = None
        else:
            selected_tangent_point = select_tangent_point_with_highest_z(tangent_points)
            line_result = line_analysis(selected_tangent_point, occluder_far)

            intersection_x0 = line_result["intersection_x0"]
            intersection_x0_z = intersection_x0[1] if intersection_x0 is not None else None
            angle_with_x0_deg = line_result["angle_with_x0_deg"]
            angle_with_forward_deg = line_result["angle_with_forward_deg"]

        rows.append(
            {
                "circle_center_x": circle_center_x,
                "circle_center_z": circle_center_z,
                "scaled_radius": scaled_radius,
                "scaled_height": scaled_height,
                "scaled_half_height": scaled_half_height,
                "intersection_x0_z": intersection_x0_z,
                "angle_vertical_deg": angle_with_x0_deg,
                "angle_with_forward_deg": angle_with_forward_deg,
            }
        )

    return pd.DataFrame(rows)


def write_results_to_excel(dataframe, output_path):
    output_path = Path(output_path)
    dataframe.to_excel(output_path, index=False)
    return output_path


def run_analysis(params):
    observer_location = params["observer_location"]
    circle_center = params["circle_center"]
    occluder_far = params["occluder_far"]
    distance_ref = params["distance_ref"]
    radius_ref = params["radius_ref"]
    height_ref = params["height_ref"]
    x_samples = params["x_samples"]

    vx, vz = observer_to_circle_vector(observer_location, circle_center)
    print("Observer -> circle center vector:", (vx, vz))

    print("\nPoints on observer -> circle center line:")
    for x in x_samples:
        z = z_on_observer_circle_line_at_x(observer_location, circle_center, x)
        print(f"x = {x:.2f} -> z = {z:.5f}")

    distance_new = circle_center[0]
    radius_new = scale_size_to_constant_retinal_size(radius_ref, distance_ref, distance_new)
    height_new = scale_size_to_constant_retinal_size(height_ref, distance_ref, distance_new)
    half_height_new = height_new / 2.0

    print("\nScaled sizes for constant retinal size:")
    print(f"Radius (new): {radius_new:.6f}")
    print(f"Height (new): {height_new:.6f}")
    print(f"Half-height (new): {half_height_new:.6f}")

    tangent_points = tangent_points_from_circle_and_point(circle_center, radius_new, occluder_far)
    print("\nTangent points from occluder_far to circle:")
    if tangent_points is None:
        print("  No tangents: occluder_far is inside the circle.")
        return

    for i, tangent_point in enumerate(tangent_points, start=1):
        print(f"  Tangent {i}: {tangent_point}")

    selected_tangent_point = select_tangent_point_with_highest_z(tangent_points)
    print("\nSelected tangent point with highest z:")
    print(f"  selected_tangent_point: {selected_tangent_point}")

    line_result = line_analysis(selected_tangent_point, occluder_far)
    print("\nSelected tangent point -> occluder_far line analysis:")
    print(f"  line_points: {line_result['line_points']}")
    print(f"  slope: {line_result['slope']}")
    print(f"  intersection_x0: {line_result['intersection_x0']}")
    print(f"  angle_with_x0_deg: {line_result['angle_with_x0_deg']:.6f}")

    results_table = build_results_table(params)
    output_path = write_results_to_excel(results_table, params["excel_output_path"])
    print("\nExcel output written to:")
    print(f"  {output_path}")

def plot_angle_vs_x(params):
    import numpy as np

    xs = np.linspace(2.2, 10.0, 500)
    angles = []

    for x in xs:
        z = z_on_observer_circle_line_at_x(
            params["observer_location"],
            params["circle_center"],
            x,
        )

        circle_center = (x, z)

        radius = scale_size_to_constant_retinal_size(
            params["radius_ref"],
            params["distance_ref"],
            x,
        )

        tangents = tangent_points_from_circle_and_point(
            circle_center,
            radius,
            params["occluder_far"],
        )

        if tangents is None:
            angles.append(float("nan"))
        else:
            t = select_tangent_point_with_highest_z(tangents)
            result = line_analysis(t, params["occluder_far"])
            angles.append(result["angle_with_forward_deg"])

    plt.figure()
    plt.plot(xs, angles)

    plt.axhline(60)
    plt.axhline(120)

    plt.xlabel("circle_center_x")
    plt.ylabel("angle_with_forward_deg")
    plt.title("Angle (forward) vs Circle Center X")

    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_analysis(PARAMS)
    plot_angle_vs_x(PARAMS)



