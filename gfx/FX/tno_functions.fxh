Code
[[

]]


PixelShader = {
Code
[[
float determineValue(float2 Offset, float2 NextOffset)
{
	float difference = NextOffset.x - Offset.x;
	if(difference < 0){
		difference *= -1.f;
	}
	float noOfFrames = 1.f/difference;
	float value = 0.f;
	
	if(NextOffset.x > Offset.x){
		value = NextOffset.x * noOfFrames;
	}
	else{
		value = Offset.x * noOfFrames;
	}
	return value;
}

float atan2TNO(float2 TexCoord)
{
	float degree = 0.f;
	float pi = 3.14159265f;
	float pi2 = 2*pi;
	TexCoord *= -1.f;
	if(TexCoord.x > 0){
		degree = atan(TexCoord.x/TexCoord.y) - pi;
		if(degree < -pi){
			degree += pi;
		}
	}
	else if(TexCoord.x < 0 && TexCoord.y >= 0){
		degree = atan(TexCoord.x/TexCoord.y) + pi;
	}
	else if(TexCoord.y < 0 && TexCoord.x < 0){
		degree = atan(TexCoord.x/TexCoord.y);
	}
	else if(TexCoord.x == 0 && TexCoord.y > 0){
		degree = -pi/2.f;
	}
	else if(TexCoord.x == 0 && TexCoord.y < 0){
		degree = pi/2.f;
	}
	else{
		degree = 0.f;
	}
	degree += 0;
	if(degree > pi2){
		degree -= pi2;
	}
	return degree;
}
]]
}
