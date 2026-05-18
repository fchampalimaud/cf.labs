# Testing occlusion angles

import math
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

### Initial Parameters
PARAMS = {
    "observer_location": (0.0, 0.0),
    "circle_center": (2.2, 2.57963777777778),
    "distance_ref": 1.0,
    "radius_ref": 0.075,
    "height_ref": 0.37,
    "occluder_near": (1.4, 2.30829),
    "occluder_far": (1.4, 2.86829),
    "x_samples": [2.2, 2.3, 2.4, 2.41, 2.42, 2.43, 2.44, 2.45, 2.46, 2.47, 2.48, 2.49, 2.5, 2.544912, 2.6, 2.7, 2.8, 2.9, 3.015],
    "excel_output_path": "motion_parallax_results.xlsx",
}


def observer_to_circle_vector(observer_location, circle_center):
    vx = circle_center[0] - observer_location[0]
    vz = circle_center[1] - observer_location[1]
    return vx, vz


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

    val = max(0.0, d2 - radius * radius)
    mu = (radius / d) * math.sqrt(val)

    ox = mu * perp_x
    oy = mu * perp_y

    t1 = (bx + ox, by + oy)
    t2 = (bx - ox, by - oy)
    return [t1, t2]


def line_analysis(point_a, point_b):
    ax, ay = point_a
    bx, by = point_b

    dx = bx - ax
    dy = by - ay

    if dx == 0:
        slope = math.inf
        y_intercept = None
    else:
        slope = dy / dx
        y_intercept = ay - slope * ax

    angle_forward = 180 - abs(math.degrees(math.atan2(dx, dy)))
    angle_vertical = math.degrees(math.atan2(abs(dx), abs(dy)))

    return {
        "slope": slope,
        "intersection_x0": (0, y_intercept) if y_intercept is not None else None,
        "angle_with_x0_deg": angle_vertical,
        "angle_with_forward_deg": angle_forward,
    }


# --- NEW: analyze both tangents ---
def analyze_tangents_to_point(circle_center, radius, target_point):
    tangents = tangent_points_from_circle_and_point(
        circle_center,
        radius,
        target_point,
    )

    if tangents is None:
        return [None, None]

    results = []
    for t in tangents:
        line_result = line_analysis(t, target_point)

        intersection_x0 = line_result["intersection_x0"]
        intersection_x0_z = (
            intersection_x0[1] if intersection_x0 is not None else None
        )

        results.append({
            "angle_forward": line_result["angle_with_forward_deg"],
            "intersection_x0_z": intersection_x0_z,
        })

    while len(results) < 2:
        results.append(None)

    return results


def select_tangent_point_with_highest_z(tangent_points):
    return max(tangent_points, key=lambda point: point[1])


def build_results_table(params):
    observer_location = params["observer_location"]
    base_circle_center = params["circle_center"]
    occluder_far = params["occluder_far"]
    occluder_near = params["occluder_near"]
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

        # --- FAR OCCLUDER (existing logic) ---
        tangent_points = tangent_points_from_circle_and_point(
            current_circle_center,
            scaled_radius,
            occluder_far,
        )

        if tangent_points is None:
            intersection_x0_z_far = None
            angle_forward_far = None
        else:
            selected_tangent_point = select_tangent_point_with_highest_z(tangent_points)
            line_result = line_analysis(selected_tangent_point, occluder_far)

            intersection_x0 = line_result["intersection_x0"]
            intersection_x0_z_far = (
                intersection_x0[1] if intersection_x0 is not None else None
            )
            angle_forward_far = line_result["angle_with_forward_deg"]

        # --- NEW: NEAR OCCLUDER (both tangents) ---
        near_tangents = analyze_tangents_to_point(
            current_circle_center,
            scaled_radius,
            occluder_near,
        )

        rows.append(
            {
                "circle_center_x": circle_center_x,
                "circle_center_z": circle_center_z,
                "scaled_radius": scaled_radius,
                "scaled_height": scaled_height,
                "scaled_half_height": scaled_half_height,

                # Far occluder
                "reappearance_angle": angle_forward_far,
                "reappearance_location": intersection_x0_z_far,

                # Near occluder - tangent 1
                "full_occlusion_angle": (
                    near_tangents[0]["angle_forward"] if near_tangents[0] else None
                ),
                "full_occlusion_location": (
                    near_tangents[0]["intersection_x0_z"] if near_tangents[0] else None
                ),

                # Near occluder - tangent 2
                "partial_occlusion_angle": (
                    near_tangents[1]["angle_forward"] if near_tangents[1] else None
                ),
                "partial_occlusion_location": (
                    near_tangents[1]["intersection_x0_z"] if near_tangents[1] else None
                ),
            }
        )

    return pd.DataFrame(rows)


def write_results_to_excel(dataframe, output_path):
    output_path = Path(output_path)
    dataframe.to_excel(output_path, index=False)
    return output_path


def run_analysis(params):
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