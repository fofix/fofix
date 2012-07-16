uniform float ambientGlow;
uniform vec4 color;
uniform float glowStrength;
uniform float ambientGlowHeightScale;
uniform float glowFallOff;
uniform float height;
uniform float sampleDist;
uniform float speed;
uniform float vertNoise;
uniform float time;
uniform float fading;
uniform bool fixalpha;
uniform sampler3D Noise3D;

varying vec2 vTexCoord;

void main()
{
  if (color.a < 0.001) {
    gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
  } else {
    vec2 t = vec2(speed * time * 0.5871 - vertNoise * abs(vTexCoord.y), speed * time);

    float xs0 = vTexCoord.x - sampleDist;
    float xs1 = vTexCoord.x;
    float xs2 = vTexCoord.x + sampleDist;

    float noise0 = texture3D(Noise3D, vec3(xs0, t)).x;
    float noise1 = texture3D(Noise3D, vec3(xs1, t)).x;
    float noise2 = texture3D(Noise3D, vec3(xs2, t)).x;

    float mid0 = height * (noise0 * 2.0 - 1.0) * (1.0 - xs0 * xs0);
    float mid1 = height * (noise1 * 2.0 - 1.0) * (1.0 - xs1 * xs1);
    float mid2 = height * (noise2 * 2.0 - 1.0) * (1.0 - xs2 * xs2);

    float dist0 = abs(vTexCoord.y - mid0);
    float dist1 = abs(vTexCoord.y - mid1);
    float dist2 = abs(vTexCoord.y - mid2);

    float glow = 1.0 - pow(0.25 * (dist0 + 2.0 * dist1 + dist2), glowFallOff);

    float ambGlow = ambientGlow * (1.0 - xs1 * xs1) * (1.0 - abs(ambientGlowHeightScale * vTexCoord.y));

    float fog = min(1.0, fading * (1.0 - abs(vTexCoord.x)));
    vec4 col = (glowStrength * glow * glow + ambGlow) * vec4(color.rgb, color.a * fog * 10.0);
    if (fixalpha) {
      float alpha = max(max(col.r, col.g), col.b);
      col.a = alpha * fog;
      if (col.a < 1.0)
        col.rgb = col.rgb / col.a;

    }

    gl_FragColor = col;
  }
  //gl_FragColor =  vec4(1.0,1.0,0.0,1.0);


  //vec4 tex = texture2D(Tex2D,vTexCoord);
  //vec4 tex = texture3D(Tex3D,vec3(vTexCoord.xy*2,fract(time)));
  //float intensity = (tex[0] + tex[1] + tex[2] + tex[3]) * 1.5;
  //gl_FragColor = vec4(tex.rgb,0.2);
}
