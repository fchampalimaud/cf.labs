#version 330 core

layout(location = 0) in vec3 position; // vertex position in model space
out vec2 texCoord;

uniform float height; // cylinder height (e.g., 2.0 if from -1 to +1)

void main() {
    // Calculate the angle around Y-axis for U (wraps from 0 to 1)
    float u = atan(position.x, position.z) / (2.0 * 3.1415926) + 0.5;

    // Calculate V as the normalized height coordinate (0 to 1)
    float v = (position.y + height * 0.5) / height;

    texCoord = vec2(u, v);

    // Transform vertex position to clip space (add your model-view-projection matrices)
    // For example:
    // gl_Position = projection * view * model * vec4(position, 1.0);
}
