#version 330 core

in vec2 texCoord;              // from vertex shader
out vec4 fragColor;            // output color

uniform sampler2D imageTex;    // texture from Bonsai

void main() {
    vec2 centered = texCoord - vec2(0.5);       // shift UVs to center (0,0)
    if (length(centered) > 0.5) discard;         // mask outside circular area
    fragColor = texture(imageTex, texCoord);     // sample the texture
}
