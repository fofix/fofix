uniform float scale;
uniform vec2 offset;
uniform vec2 scalexy;
uniform bool solofx;

varying vec2 vTexCoord;

void main()
{
  vec3 Position = gl_Vertex.xyz;

  //gl_Position = vec4(Position.xyz, 1.0);

  if (solofx)
    vTexCoord = Position.zx;
  else
    vTexCoord = Position.xy;

  vTexCoord += offset;
  vTexCoord /= scalexy;
  gl_Position = ftransform();
}
