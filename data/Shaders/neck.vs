uniform float offset;
uniform float time;
uniform float F1;
uniform float F2;
uniform float F3;
uniform float F4;
uniform float F5;
uniform float fade;

varying vec4 col;

void main()
{     
        col = vec4(0.0,1.0,0.0,0.2) / (time - F1 + fade);
        col = col + vec4(1.0,0.0,0.0,0.2) / (time - F2 + fade);
        col = col + vec4(1.0,1.0,0.0,0.2) / (time - F3 + fade);
        col = col + vec4(0.0,0.0,1.0,0.2) / (time - F4 + fade);
        col = col + vec4(0.0,1.0,1.0,0.2) / (time - F5 + fade);
        col = col*0.4;

	gl_Position = ftransform();
	col.a = 0.3*col.a*(4.0-gl_Vertex.z/2);
} 