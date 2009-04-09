uniform float scale;
uniform vec2 offset;

varying vec2 vTexCoord;

void main()
{
   vec3 Position = gl_Vertex.xyz;

   gl_Position = vec4(Position.xyz, 1.0);
   vTexCoord = Position.xy*scale;
   vTexCoord.x += offset.x;
   vTexCoord.y += offset.y;
} 