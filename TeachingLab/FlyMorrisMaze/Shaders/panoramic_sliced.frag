#version 400

in vec2 uv;               // from vertex shader (vp). we use u = uv.x*0.5+0.5
out vec4 fragColor;

uniform samplerCube cubeMap;
uniform float fovTotal = 270.0;   // total panorama span (degrees)
uniform float sliceAngle = 90.0;  // per-slice width (degrees)
uniform int sliceIndex = 2;       // 0=left,1=front,2=right
uniform float maxY = 0.5;        // vertical half-height of cylinder

void main()
{
    // normalized coords [0,1]
    float u = uv.x * 0.5 + 0.5;
    float v = uv.y * 0.5 + 0.5;

    // compute start of total FOV (centered)
    float startDeg = -0.5 * fovTotal;             // -135 for fovTotal=270

    // compute this slice start (degrees)
    float sliceStart = startDeg + float(sliceIndex) * sliceAngle;

    // theta (degrees) across this slice
    float thetaDeg = sliceStart + u * sliceAngle; // maps u∈[0,1] -> sliceStart..sliceStart+sliceAngle
    float theta = radians(thetaDeg);

    // linear vertical mapping to [-maxY, +maxY]
    float y = (v - 0.5) * 2.0 * maxY;

    // lateral XZ direction (ignore ceiling/floor)
    vec3 dir = normalize(vec3(sin(theta), 0.0, cos(theta)));

    // plug linear y into direction for cubemap sample
    dir.y = clamp(y, -maxY, maxY);

    fragColor = texture(cubeMap, dir);
}
