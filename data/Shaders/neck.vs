uniform float stretch;
uniform float offset;
uniform float time;
uniform float F1;
uniform float F2;
uniform float F3;
uniform float F4;
uniform float F5;
uniform float mult;
uniform float fade;

varying vec3 lightDir,normal;
varying vec3 pos;
varying vec4 col;
varying float alpha;

void main()
{
        vec3 a = gl_Vertex.xyz/stretch;
        a.x = a.x - 0.5;
        a.z = a.z / 2 + offset;
        pos = a.xyz;
        
        col.r = mult / (time - F2 + fade) + mult / (time - F3 + fade) + 0.5 * mult / (time - F5 + fade);
        col.g = mult / (time - F1 + fade) + mult / (time - F3 + fade);
        col.b = mult / (time - F4 + fade) + mult / (time - F5 + fade);
        
        alpha = 1.5-pos.z + offset;
	normal = normalize(gl_NormalMatrix * gl_Normal);
	lightDir = normalize(vec3(gl_LightSource[0].position));
	
	gl_TexCoord[0] = gl_MultiTexCoord0;
	gl_Position = ftransform();
} 