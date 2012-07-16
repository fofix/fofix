uniform vec2 offset;
uniform vec2 scalexy;

varying vec3 pos;
varying vec2 vTexCoord;


void main()
{
  gl_Position = ftransform();
  pos = gl_Vertex.xyz;

  vTexCoord = pos.zx;

  vTexCoord += offset;
  vTexCoord /= scalexy;
}
