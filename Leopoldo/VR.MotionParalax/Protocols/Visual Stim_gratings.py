# ============================================================
# 🎯 VISUAL STIMULUS GENERATOR - CONFIGURATION SECTION
# ============================================================

# Screen and viewing parameters
diag_in = 27            # 27-inch screen
resolution = (1920,1080)
viewing_distance_cm = 15.0
spatial_freq_cpd = 0.5  # cycles per degree for gratings

# Requested grating physical sizes (width_cm, height_cm)
requested_sizes_cm = [(40.0, 35.0), (15.0, 35.0), (2.0, 11.0)]

# Output directory
outdir = r"C:\Users\Openlab CC\Desktop\gratings_output_0.5cpd"

# ============================================================
# 🎨 CHOOSE YOUR PATTERNS HERE - Set True/False for each type
# ============================================================

# Basic gratings (oriented lines)
GENERATE_GRATINGS = False
GRATING_ORIENTATIONS = {
    "vertical": 0,      
    "horizontal": 90,   
    "diag_45": 45,      
    "diag_135": -45,
}

# Basic geometric shapes
GENERATE_CIRCLES = True
GENERATE_SQUARES = True
GENERATE_TRIANGLES = True
GENERATE_STARS = True
GENERATE_DIAMONDS = True
GENERATE_HEXAGONS = True

# Wave and ripple patterns
GENERATE_CONCENTRIC = False
GENERATE_RADIAL = False
GENERATE_SPIRAL = False
GENERATE_CHECKERBOARD = False

# Complex patterns
GENERATE_CROSSHATCH = False
GENERATE_ZIGZAG = False
GENERATE_BRICK = False

# Random patterns
GENERATE_RANDOM_DOTS = False
GENERATE_POLKA_DOTS = False

# ============================================================
# 🔧 PATTERN PARAMETERS (Adjust sizes and spacing)
# ============================================================

# Shape parameters - ADAPTIVE based on object size
def get_shape_spacing(w_cm):
    """Calculate appropriate spacing based on object width"""
    if w_cm == 2.0:     # 2cm objects
        return 25       # Very close spacing for tiny objects
    elif w_cm == 15.0:  # 15cm objects  
        return 120      # Medium spacing - fewer circles
    elif w_cm == 40.0:  # 40cm objects
        return 250      # Large spacing - very few circles
    else:
        return 100      # Default fallback

SHAPE_SIZE = 0.35       # Shape size as fraction of spacing

# Wave pattern parameters
WAVE_FREQUENCY = 0.08   # For spiral patterns
NUM_RAYS = 46          # For radial patterns
RING_WIDTH = 30        # For concentric circles

# Random pattern parameters
DOT_DENSITY = 0.01    # Density for random dots (0.001 = sparse, 0.01 = dense)

# Color values (0=black, 128=gray, 255=white)
SHAPE_COLOR = (0, 128, 0)      # GREEN shapes (RGB)
BACKGROUND_COLOR = 255         # White background

# NEW: Grating-specific colors (RGB values)
GRATING_STRIPE_COLOR = (0, 0, 255)    # Blue stripes
GRATING_BACKGROUND_COLOR = (255, 255, 255)  # White background
USE_COLOR_GRATINGS = True  # Set to False for grayscale gratings
USE_COLOR_SHAPES = True    # NEW: Enable colored shapes

# ============================================================
# 📝 SCRIPT IMPLEMENTATION (Don't modify below unless needed)
# ============================================================

# Libraries
import numpy as np, math, os
from PIL import Image

# Build pattern dictionary based on user selections
orientations = {}

if GENERATE_GRATINGS:
    orientations.update(GRATING_ORIENTATIONS)

pattern_types = [
    (GENERATE_CIRCLES, "circles", "circle"),
    (GENERATE_SQUARES, "squares", "square"),
    (GENERATE_TRIANGLES, "triangles", "triangle"),
    (GENERATE_STARS, "stars", "star"),
    (GENERATE_DIAMONDS, "diamonds", "diamond"),
    (GENERATE_HEXAGONS, "hexagons", "hexagon"),
    (GENERATE_CONCENTRIC, "concentric", "concentric"),
    (GENERATE_RADIAL, "radial", "radial"),
    (GENERATE_SPIRAL, "spiral", "spiral"),
    (GENERATE_CHECKERBOARD, "checkerboard", "checkerboard"),
    (GENERATE_CROSSHATCH, "crosshatch", "crosshatch"),
    (GENERATE_ZIGZAG, "zigzag", "zigzag"),
    (GENERATE_BRICK, "brick", "brick"),
    (GENERATE_RANDOM_DOTS, "random_dots", "random_dots"),
    (GENERATE_POLKA_DOTS, "polka_dots", "polka_dots"),
]

for enabled, name, pattern_type in pattern_types:
    if enabled:
        orientations[name] = pattern_type

# Check if user selected anything
if not orientations:
    print("❌ No patterns selected! Please set at least one GENERATE_* to True.")
    exit()

print(f"✅ Generating {len(orientations)} patterns: {list(orientations.keys())}")

# Compute physical screen size from diagonal and 16:9 aspect ratio
diag_cm = diag_in * 2.54
w_ratio, h_ratio = 16, 9
screen_width_cm = diag_cm * (w_ratio / math.sqrt(w_ratio**2 + h_ratio**2))
screen_height_cm = diag_cm * (h_ratio / math.sqrt(w_ratio**2 + h_ratio**2))

px_w, px_h = resolution
px_per_cm_x = px_w / screen_width_cm
px_per_cm_y = px_h / screen_height_cm

# Degrees per cm at viewing distance (exact formula)
def degrees_for_length_cm(length_cm, distance_cm):
    return 2.0 * math.degrees(math.atan((length_cm/2.0) / distance_cm))

deg_per_cm = degrees_for_length_cm(1.0, viewing_distance_cm)
cycles_per_cm = spatial_freq_cpd / deg_per_cm

# Prepare output directory
os.makedirs(outdir, exist_ok=True)

report_lines = []
saved_files = []

# Pattern generation functions
def generate_pattern(X, Y, pattern_type, cycles_per_pixel=None, current_shape_spacing=80):
    """Generate different pattern types based on coordinates X, Y"""
    
    if isinstance(pattern_type, (int, float)):  # Grating angles
        # Original grating code for angles
        theta = math.radians(pattern_type)
        U = X * math.cos(theta) + Y * math.sin(theta)
        freq = cycles_per_pixel
        pattern = np.sign(np.sin(2.0 * math.pi * freq * U))
        return pattern > 0
    
    elif pattern_type == "circle":
        # Generate exactly 4 randomly placed circles
        np.random.seed(42)  # For reproducible patterns
        pattern_mask = np.zeros_like(X, dtype=bool)
        
        # Calculate appropriate circle size based on PHYSICAL dimensions, not pixel dimensions
        # Use the actual physical size to determine circle radius
        circle_radius_cm = min(w_cm, h_cm) * 0.25  # 25% of smallest dimension
        
        # Convert physical radius to pixels (accounting for different X/Y pixel densities)
        circle_radius_px_x = circle_radius_cm * px_per_cm_x
        circle_radius_px_y = circle_radius_cm * px_per_cm_y
        
        # Create margins in physical space
        margin_cm = circle_radius_cm * 2
        margin_px_x = margin_cm * px_per_cm_x
        margin_px_y = margin_cm * px_per_cm_y
        
        # Create 4 random circle positions
        for i in range(4):
            # Random position within bounds (in pixel coordinates)
            center_x = np.random.uniform(-canvas_w/2 + margin_px_x, canvas_w/2 - margin_px_x)
            center_y = np.random.uniform(-canvas_h/2 + margin_px_y, canvas_h/2 - margin_px_y)
            
            # Create PROPER circle using ellipse equation to account for pixel density differences
            dist_x_normalized = (X - center_x) / circle_radius_px_x
            dist_y_normalized = (Y - center_y) / circle_radius_px_y
            
            # Circle equation: (x/rx)² + (y/ry)² < 1
            circle_condition = (dist_x_normalized**2 + dist_y_normalized**2) < 1
            pattern_mask |= circle_condition
        
        return pattern_mask
    
    elif pattern_type == "square":
        # Generate exactly 4 randomly placed squares
        np.random.seed(42)
        pattern_mask = np.zeros_like(X, dtype=bool)
        
        # Calculate square size in physical units
        square_size_cm = min(w_cm, h_cm) * 0.25    # 25% of smallest dimension
        square_size_px_x = square_size_cm * px_per_cm_x
        square_size_px_y = square_size_cm * px_per_cm_y
        
        margin_cm = square_size_cm * 2
        margin_px_x = margin_cm * px_per_cm_x
        margin_px_y = margin_cm * px_per_cm_y
        
        for i in range(4):
            center_x = np.random.uniform(-canvas_w/2 + margin_px_x, canvas_w/2 - margin_px_x)
            center_y = np.random.uniform(-canvas_h/2 + margin_px_y, canvas_h/2 - margin_px_y)
            
            # Create proper square accounting for pixel density
            square_mask = ((np.abs(X - center_x) < square_size_px_x/2) & 
                          (np.abs(Y - center_y) < square_size_px_y/2))
            pattern_mask |= square_mask
        
        return pattern_mask
    
    elif pattern_type == "triangle":
        scale = current_shape_spacing
        x_grid = (X // scale) * scale + scale/2
        y_grid = (Y // scale) * scale + scale/2
        rel_x = X - x_grid
        rel_y = Y - y_grid + scale/4
        triangle_height = scale * SHAPE_SIZE
        return ((rel_y > 0) & (rel_y < triangle_height) & 
                (np.abs(rel_x) < rel_y * (scale * SHAPE_SIZE / triangle_height)))
    
    elif pattern_type == "star":
        scale = current_shape_spacing
        x_grid = (X // scale) * scale + scale/2
        y_grid = (Y // scale) * scale + scale/2
        dist = np.sqrt((X - x_grid)**2 + (Y - y_grid)**2)
        angle = np.arctan2(Y - y_grid, X - x_grid)
        # Simple 5-pointed star approximation
        star_points = 5
        angle_section = (angle + np.pi) % (2 * np.pi / star_points)
        star_radius = scale * SHAPE_SIZE
        # Create star-like shape by modulating radius
        effective_radius = star_radius * (1 + 0.3 * np.cos(star_points * angle_section))
        return dist < effective_radius
    
    elif pattern_type == "diamond":
        scale = current_shape_spacing
        x_grid = (X // scale) * scale + scale/2
        y_grid = (Y // scale) * scale + scale/2
        rel_x = np.abs(X - x_grid)
        rel_y = np.abs(Y - y_grid)
        diamond_size = scale * SHAPE_SIZE
        return (rel_x + rel_y) < diamond_size
    
    elif pattern_type == "hexagon":
        scale = current_shape_spacing
        x_offset = scale * 0.866  # hex spacing
        y_offset = scale * 0.75
        row = (Y // y_offset).astype(int)
        col = ((X - (row % 2) * x_offset/2) // x_offset).astype(int)
        x_hex = col * x_offset + (row % 2) * x_offset/2
        y_hex = row * y_offset
        dist_to_hex = np.sqrt((X - x_hex)**2 + (Y - y_hex)**2)
        return dist_to_hex < scale * SHAPE_SIZE
    
    elif pattern_type == "concentric":
        center_x, center_y = 0, 0
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        return ((dist_from_center % (RING_WIDTH * 2)) < RING_WIDTH)
    
    elif pattern_type == "radial":
        center_x, center_y = 0, 0
        angle = np.arctan2(Y - center_y, X - center_x)
        ray_width = np.pi / (NUM_RAYS * 2)
        return ((angle + np.pi) % (2 * np.pi / NUM_RAYS)) < ray_width
    
    elif pattern_type == "spiral":
        center_x, center_y = 0, 0
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        angle = np.arctan2(Y - center_y, X - center_x)
        return np.sin(angle - WAVE_FREQUENCY * dist) > 0
    
    elif pattern_type == "checkerboard":
        scale = current_shape_spacing
        x_check = (X // scale).astype(int)
        y_check = (Y // scale).astype(int)
        return ((x_check + y_check) % 2) == 0
    
    elif pattern_type == "crosshatch":
        line_spacing = current_shape_spacing
        line_width = max(3, int(line_spacing * 0.1))
        vertical_lines = (X % line_spacing) < line_width
        horizontal_lines = (Y % line_spacing) < line_width
        return vertical_lines | horizontal_lines
    
    elif pattern_type == "zigzag":
        scale = current_shape_spacing
        wave_height = scale * 0.4
        zigzag_y = wave_height * np.abs(((X / scale) % 2) - 1)
        return Y > zigzag_y
    
    elif pattern_type == "brick":
        brick_w = current_shape_spacing
        brick_h = current_shape_spacing // 2
        mortar = max(2, int(brick_w * 0.05))
        
        row = (Y // brick_h).astype(int)
        col_offset = (row % 2) * (brick_w // 2)
        col = ((X - col_offset) // brick_w).astype(int)
        
        x_in_brick = (X - col_offset) % brick_w
        y_in_brick = Y % brick_h
        
        return (x_in_brick > mortar) & (x_in_brick < brick_w - mortar) & \
               (y_in_brick > mortar) & (y_in_brick < brick_h - mortar)
    
    elif pattern_type == "random_dots":
        np.random.seed(42)  # Reproducible random pattern
        
        # Create random centers
        dot_spacing = int(1.0 / np.sqrt(DOT_DENSITY))  # Average spacing between dots
        num_dots_x = canvas_w // dot_spacing
        num_dots_y = canvas_h // dot_spacing
        
        # Generate random dot positions
        pattern_mask = np.zeros_like(X, dtype=bool)
        
        for i in range(num_dots_x):
            for j in range(num_dots_y):
                # Random position within each grid cell
                center_x = (i + np.random.random()) * dot_spacing - canvas_w/2
                center_y = (j + np.random.random()) * dot_spacing - canvas_h/2
                
                # Make each dot larger (adjust this radius)
                dot_radius = 8  # Change this value: 3=small dots, 8=medium, 15=large dots
                
                dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                pattern_mask |= (dist < dot_radius)
        
        return pattern_mask
    
    elif pattern_type == "polka_dots":
        scale = current_shape_spacing
        # Regular grid with slight randomness
        np.random.seed(42)
        x_centers = (X // scale) * scale + scale/2
        y_centers = (Y // scale) * scale + scale/2
        
        # Add slight random offset to each dot
        offset_scale = scale * 0.2
        x_offset = (np.random.random(X.shape) - 0.5) * offset_scale
        y_offset = (np.random.random(Y.shape) - 0.5) * offset_scale
        
        dist = np.sqrt((X - x_centers - x_offset)**2 + (Y - y_centers - y_offset)**2)
        return dist < scale * SHAPE_SIZE
    
    else:
        # Default fallback
        return np.zeros_like(X, dtype=bool)

# Main generation loop
for (w_cm, h_cm) in requested_sizes_cm:
    # Convert requested physical size to pixel size
    req_px_w = int(round(w_cm * px_per_cm_x))
    req_px_h = int(round(h_cm * px_per_cm_y))
    
    fits = (req_px_w <= px_w and req_px_h <= px_h)
    report_lines.append(f"Requested physical size {w_cm}×{h_cm} cm -> {req_px_w}×{req_px_h} px on this 27\" screen.")
    if not fits:
        report_lines.append("Note: requested region does not fully fit; will be centered and clipped.")

    # Compute cycles for gratings
    cycles_across_width = cycles_per_cm * w_cm
    cycles_per_pixel = cycles_across_width / req_px_w if req_px_w > 0 else 0.0
    px_per_cycle = 1.0 / cycles_per_pixel if cycles_per_pixel > 0 else float('inf')
    
    report_lines.append(f"Spatial frequency: {spatial_freq_cpd} cpd -> {cycles_per_cm:.6f} cycles/cm")
    report_lines.append(f"-> {cycles_across_width:.3f} cycles across width -> {px_per_cycle:.3f} px/cycle\n")

    # Create coordinate grid
    canvas_w = max(req_px_w, px_w)
    canvas_h = max(req_px_h, px_h)
    xv = np.linspace(-canvas_w/2.0, canvas_w/2.0, canvas_w)
    yv = np.linspace(-canvas_h/2.0, canvas_h/2.0, canvas_h)
    X, Y = np.meshgrid(xv, yv)

    # Generate each pattern
    for name, pattern_type in orientations.items():
        print(f"Generating {name} pattern...")
        
        # Calculate adaptive spacing based on object width
        current_shape_spacing = get_shape_spacing(w_cm)
        
        pattern_mask = generate_pattern(X, Y, pattern_type, cycles_per_pixel, current_shape_spacing)
        
        # Apply coloring
        if isinstance(pattern_type, (int, float)) and USE_COLOR_GRATINGS:  # Colored gratings
            # Create RGB image
            img_arr = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            img_arr[pattern_mask] = GRATING_STRIPE_COLOR
            img_arr[~pattern_mask] = GRATING_BACKGROUND_COLOR
            img = Image.fromarray(img_arr, mode='RGB')
        elif USE_COLOR_SHAPES and not isinstance(pattern_type, (int, float)):  # Colored shapes
            # Create RGB image for colored shapes - INVERTED COLORS
            img_arr = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            img_arr[pattern_mask] = [BACKGROUND_COLOR, BACKGROUND_COLOR, BACKGROUND_COLOR]  # WHITE shapes
            img_arr[~pattern_mask] = SHAPE_COLOR  # GREEN background
            img = Image.fromarray(img_arr, mode='RGB')
        else:
            # Grayscale for other patterns
            img_arr = np.where(pattern_mask, 128, BACKGROUND_COLOR).astype(np.uint8)
            img = Image.fromarray(img_arr, mode='L')

        # Create final image and center
        if (isinstance(pattern_type, (int, float)) and USE_COLOR_GRATINGS) or \
           (USE_COLOR_SHAPES and not isinstance(pattern_type, (int, float))):
            # RGB image for colored gratings or shapes
            final = Image.new('RGB', (px_w, px_h), color=(127, 127, 127))  # Gray background
        else:
            # Grayscale for other patterns
            final = Image.new('L', (px_w, px_h), color=127)  # mid-gray background

        left = (canvas_w - px_w) // 2
        upper = (canvas_h - px_h) // 2
        crop = img.crop((left, upper, left + px_w, upper + px_h))
        final.paste(crop, (0, 0))
        
        # Save file
        fname = f"pattern_{int(w_cm)}x{int(h_cm)}cm_{name}_0.5cpd.png"
        fpath = os.path.join(outdir, fname)
        final.save(fpath)
        saved_files.append(fpath)

# Save report
report_path = os.path.join(outdir, "pattern_report_0.5cpd.txt")
with open(report_path, "w") as f:
    f.write("Visual Stimulus Generation Report\n")
    f.write("=" * 40 + "\n\n")
    f.write(f"Generated {len([f for f in saved_files if f.endswith('.png')])} pattern files:\n")
    for pattern_name in orientations.keys():
        f.write(f"  - {pattern_name}\n")
    f.write(f"\nParameters used:\n")
    f.write(f"  - Shape spacing (adaptive): Small objects={get_shape_spacing(15)} px, Large objects={get_shape_spacing(40)} px\n")
    f.write(f"  - Shape size: {SHAPE_SIZE} (fraction of spacing)\n")
    f.write(f"  - Shape color: {SHAPE_COLOR} (RGB green)\n")
    f.write(f"  - Background color: {BACKGROUND_COLOR} (white)\n\n")
    f.write("\n".join(report_lines))

saved_files.append(report_path)

print(f"\n✅ Successfully generated {len([f for f in saved_files if f.endswith('.png')])} pattern files!")
print(f"📁 Files saved to: {outdir}")
print(f"📊 Report saved to: {report_path}")

# Return list of saved files
saved_files