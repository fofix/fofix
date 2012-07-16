uniform vec3 note_position;
uniform vec3 light0;
uniform vec3 light1;
uniform vec3 light2;

varying vec3 vNormal;
varying vec3 vLight1;
varying vec3 vLight2;
varying vec3 vLight3;
varying vec3 vView;


void main(void)
{
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
  vNormal = gl_Normal;
  vec3 view_pos = -note_position.xyz;
  view_pos.z -= 8.0;
  view_pos.y += 4.0;
  vView = normalize(view_pos.xyz - gl_Vertex.xyz);
  vLight1 = normalize(light0.xyz - view_pos.xyz);
  vLight2 = normalize(light1.xyz - view_pos.xyz);
  vLight3 = normalize(light2.xyz - view_pos.xyz);
}
