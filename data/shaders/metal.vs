uniform vec4 view_position;
uniform vec4 light0;
uniform vec4 light1;
uniform vec4 light2;

varying vec3  vNormal;
varying vec3  vLight1;
varying vec3  vLight2;
varying vec3  vLight3;
varying vec3  vView;


void main(void)
{
   gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex; 
   vNormal = gl_Normal;
   vView = normalize( view_position.xyz - gl_Vertex.xyz );
   vLight1 = normalize(light0.xyz - gl_Vertex.xyz); 
   vLight2 = normalize(light1.xyz - gl_Vertex.xyz);
   vLight3 = normalize(light2.xyz - gl_Vertex.xyz);
}