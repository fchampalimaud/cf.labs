#version 330 core

in vec2 vp;      // provided by TexturedQuad (vertex position)
in vec2 vt;      // texture coordinate
out vec2 texCoord;

void main() {
    gl_Position = vec4(vp, 0.0, 1.0);
    texCoord = vt;
}
