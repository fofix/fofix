varying vec4 col;
varying vec3 pos;
varying vec4 failcol;

vec4 mix(in vec4 col1, in vec4 col2) 
{
  vec4 color;
  col1 = max(col1,0.0);
  col1 = min(col1,1.0);
  col2 = max(col2,0.0);
  col2 = min(col2,1.0);
  float a1 = (1.0-col2.a)*col1.a;
  color.rgb = col1.rgb*a1+col2.rgb*col2.a;
  color.a = col2.a+a1;
  return(color);
}

void main()
{
  vec4 color = failcol;
  color.a = color.a*(abs(pos.x)-1.0);
  color = mix(col,color);
  gl_FragColor = color;
}