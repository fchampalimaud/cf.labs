#version 400
in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D tex;      // plane texture
uniform vec4 solidColor = vec4(1.0,0.0,0.0,0.5);    // cylinders

void main() {
   fragColor = solidColor;
}
