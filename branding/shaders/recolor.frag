#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 accentA;
    vec4 accentB;
};

layout(binding = 1) uniform sampler2D source;

vec3 rgbToHsv(vec3 color)
{
    const vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(
        vec4(color.bg, K.wz),
        vec4(color.gb, K.xy),
        step(color.b, color.g)
    );
    vec4 q = mix(
        vec4(p.xyw, color.r),
        vec4(color.r, p.yzx),
        step(p.x, color.r)
    );

    float chroma = q.x - min(q.w, q.y);
    float epsilon = 1.0e-6;
    return vec3(
        abs(q.z + (q.w - q.y) / (6.0 * chroma + epsilon)),
        chroma / (q.x + epsilon),
        q.x
    );
}

vec3 hsvToRgb(vec3 hsv)
{
    vec3 phase = abs(fract(hsv.xxx + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0);
    return hsv.z * mix(vec3(1.0), clamp(phase - 1.0, 0.0, 1.0), hsv.y);
}

void main()
{
    vec4 sampleColor = texture(source, qt_TexCoord0);
    float alpha = sampleColor.a;

    // Qt Quick layer textures use premultiplied alpha. Work in straight RGB
    // so that transparent logo edges keep their original antialiasing.
    vec3 originalRgb = alpha > 1.0e-5
        ? sampleColor.rgb / alpha
        : vec3(0.0);

    vec3 hsv = rgbToHsv(originalRgb);
    vec3 colorA = accentA.a > 1.0e-5 ? accentA.rgb / accentA.a : accentA.rgb;
    vec3 colorB = accentB.a > 1.0e-5 ? accentB.rgb / accentB.a : accentB.rgb;

    float hueA = rgbToHsv(colorA).x;
    float hueB = rgbToHsv(colorB).x;

    // The supplied LEOS artwork uses a saturated cyan/blue-to-magenta
    // neon range. Map that range smoothly to the user's A-to-B hue arc.
    float gradientPosition = smoothstep(0.46, 0.91, hsv.x);
    float hueDelta = fract(hueB - hueA + 0.5) - 0.5;
    float targetHue = fract(hueA + hueDelta * gradientPosition + 1.0);

    vec3 remappedRgb = hsvToRgb(vec3(targetHue, hsv.y, hsv.z));

    // Leave neutral blacks, greys, whites and skin/wood tones untouched.
    float saturationMask = smoothstep(0.16, 0.38, hsv.y);
    float hueMask = smoothstep(0.42, 0.49, hsv.x)
                  * (1.0 - smoothstep(0.92, 0.99, hsv.x));
    float colorMask = saturationMask * hueMask;

    vec3 outputRgb = mix(originalRgb, remappedRgb, colorMask);
    fragColor = vec4(outputRgb * alpha, alpha) * qt_Opacity;
}
