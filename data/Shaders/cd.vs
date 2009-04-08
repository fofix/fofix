varying float alpha;

void main()
{
	gl_Position = ftransform();
	gl_Position.z = gl_Position.z-0.01;
	vec3 pos = gl_Vertex.xyz/4.5;
	pos.xyz = abs(pos.xyz-0.5);
	alpha = (pos.g-pos.r);
} 