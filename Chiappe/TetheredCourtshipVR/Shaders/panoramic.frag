#version 400
in vec2 uv;
out vec4 fragColor;

uniform samplerCube cubeMap;
uniform float fov = 270.0;

void main()
{
    float u = uv.x * 0.5 + 0.5;
    float v = uv.y * 0.5 + 0.5;

    float theta = (u - 0.5) * radians(fov);

    // Compute lateral XZ direction
    vec3 dir = normalize(vec3(sin(theta), 0.0, cos(theta)));

    // Map vertical position into cylinder height [-0.5,0.5]
    float maxY = 0.5;  // adjust as needed for arena height
    dir.y = (v - 0.5) * 2.0 * maxY;

    // Clamp so y does not exceed the lateral extent
    dir.y = clamp(dir.y, -maxY, maxY);

    fragColor = texture(cubeMap, dir);
}
