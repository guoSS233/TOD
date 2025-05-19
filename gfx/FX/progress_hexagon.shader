Includes = {
}

PixelShader =
{
	Samplers =
	{
		TextureOne =
		{
			Index = 0
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
		TextureTwo =
		{
			Index = 1
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
	}
}


VertexStruct VS_INPUT
{
    float4 vPosition  : POSITION;
    float2 vTexCoord  : TEXCOORD0;
};

VertexStruct VS_OUTPUT
{
    float4  vPosition : PDX_POSITION;
    float2  vTexCoord0 : TEXCOORD0;
};


ConstantBuffer( 0, 0 )
{
	float4x4 WorldViewProjectionMatrix; 
	float4 vFirstColor;
	float4 vSecondColor;
	float CurrentState;
};


VertexShader =
{
	MainCode VertexShader
	[[
		
		VS_OUTPUT main(const VS_INPUT v )
		{
			VS_OUTPUT Out;
		   	Out.vPosition  = mul( WorldViewProjectionMatrix, v.vPosition );
			Out.vTexCoord0  = v.vTexCoord - 0.5f;
		
			return Out;
		}
		
	]]
}

PixelShader =
{
	MainCode PixelColor
	[[
		
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			if( v.vTexCoord0.x <= CurrentState )
				return vFirstColor;
			else
				return vSecondColor;
		}
		
	]]

	MainCode PixelTexture
	[[
		
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float2 pointOne = float2(-0.25f,0.44f); //Upper 2 points
			float2 pointTwo = float2(0.25f,0.44f);
			
			float2 pointFive = float2(-0.25f,-0.44f);
			float2 pointFour = float2(0.25f,-0.44f); //Lower 2 points
			
			float2 pointSix = float2(-0.5f,0.f); //Middle 2 points
			float2 pointThree = float2(0.5f,0.f);
			
			float value = CurrentState * 1000000.f;
			float firstProgress = floor(value / 100000.f) / 10.f;
			float secondProgress = (floor(value / 10000.f) - (firstProgress * 100.f)) / 10.f;
			float thirdProgress = (floor(value / 1000.f) - (firstProgress * 1000.f) - (secondProgress * 100.f)) / 10.f;
			float fourthProgress = (floor(value / 100.f) - (firstProgress * 10000.f) - (secondProgress * 1000.f) - (thirdProgress * 100.f)) / 10.f;
			float fifthProgress = (floor(value / 10.f) - (firstProgress * 100000.f) - (secondProgress * 10000.f) - (thirdProgress * 1000.f) - (fourthProgress * 100.f)) / 10.f;
			float sixthProgress = (value - (firstProgress * 1000000.f) - (secondProgress * 100000.f) - (thirdProgress * 10000.f) - (fourthProgress * 1000.f) - (fifthProgress * 100.f)) / 10.f;
			
			pointOne *=(firstProgress + 0.1f);
			pointTwo *=(secondProgress + 0.1f);
			pointThree *=(thirdProgress + 0.1f);
			pointFour *=(fourthProgress + 0.1f);
			pointFive *=(fifthProgress + 0.1f);
			pointSix *=(sixthProgress + 0.1f);
			
			float infGrad2 = 0.f;
			float infGrad3 = 0.f;
			float infGrad5 = 0.f;
			float infGrad6 = 0.f;
			
			float checkVar = 0.f;
			
			float gradOne = (pointTwo.y - pointOne.y)/(pointTwo.x - pointOne.x);
			float cOne = pointOne.y - (gradOne * pointOne.x);
			float2 lineOne = float2(gradOne,cOne);
			
			float gradTwo = (pointThree.y - pointTwo.y)/(pointThree.x - pointTwo.x);
			float cTwo = pointTwo.y - (gradTwo * pointTwo.x);
			if (pointTwo.x == pointThree.x) {
				infGrad2 = 1.f;
				cTwo = pointTwo.x;
			}
			float2 lineTwo = float2(gradTwo,cTwo);
			
			float gradThree = (pointFour.y - pointThree.y)/(pointFour.x - pointThree.x);
			float cThree = pointThree.y - (gradThree * pointThree.x);
			if (pointThree.x == pointFour.x) {
				infGrad3 = 1.f;
				cThree = pointThree.x;
			}
			float2 lineThree = float2(gradThree,cThree);
			
			float gradFour = (pointFive.y - pointFour.y)/(pointFive.x - pointFour.x);
			float cFour = pointFour.y - (gradFour * pointFour.x);
			float2 lineFour = float2(gradFour,cFour);
			
			float gradFive = (pointSix.y - pointFive.y)/(pointSix.x - pointFive.x);
			float cFive = pointFive.y - (gradFive * pointFive.x);
			if (pointFive.x == pointSix.x) {
				infGrad5 = 1.f;
				cFive = pointFive.x;
			}
			float2 lineFive = float2(gradFive,cFive);
			
			float gradSix = (pointOne.y - pointSix.y)/(pointOne.x - pointSix.x);
			float cSix = pointSix.y - (gradSix * pointSix.x);
			if (pointSix.x == pointOne.x) {
				infGrad6 = 1.f;
				cSix = pointSix.x;
			}
			float2 lineSix = float2(gradSix,cSix);
			
			float4 colour = float4(0,0,0,0);
			
			
			float2 dist1 = v.vTexCoord0 - pointOne;
			float2 dist2 = v.vTexCoord0 - pointTwo;
			float2 dist3 = v.vTexCoord0 - pointThree;
			float2 dist4 = v.vTexCoord0 - pointFour;
			float2 dist5 = v.vTexCoord0 - pointFive;
			float2 dist6 = v.vTexCoord0 - pointSix;
			
			float l1 = length(dist1);
			float l2 = length(dist2);
			float l3 = length(dist3);
			float l4 = length(dist4);
			float l5 = length(dist5);
			float l6 = length(dist6);
			
			if ((((v.vTexCoord0.x * lineOne.x) + lineOne.y - v.vTexCoord0.y) > 0) && (lineOne.x > 0)) {
				checkVar += 1.f;
			}
			if ((((v.vTexCoord0.x * lineOne.x) + lineOne.y - v.vTexCoord0.y) > 0) && (lineOne.x < 0)) {
				checkVar += 1.f;
			}
			
			if (infGrad2 == 1) {
				if (v.vTexCoord0.x < lineTwo.y) {
					checkVar += 1.f;
				}
			} else {
				if ((((v.vTexCoord0.x * lineTwo.x) + lineTwo.y - v.vTexCoord0.y) < 0) && (lineTwo.x > 0)) {
					checkVar += 1.f;
				}
				if ((((v.vTexCoord0.x * lineTwo.x) + lineTwo.y - v.vTexCoord0.y) > 0) && (lineTwo.x < 0)) {
					checkVar += 1.f;
				}
			}
			
			if (infGrad3 == 1) {
				if (v.vTexCoord0.x < lineThree.y) {
					checkVar += 1.f;
				}
			} else {
				if ((((v.vTexCoord0.x * lineThree.x) + lineThree.y - v.vTexCoord0.y) < 0) && (lineThree.x > 0)) {
					checkVar += 1.f;
				}
				if ((((v.vTexCoord0.x * lineThree.x) + lineThree.y - v.vTexCoord0.y) > 0) && (lineThree.x < 0)) {
					checkVar += 1.f;
				}
			}
			
			if ((((v.vTexCoord0.x * lineFour.x) + lineFour.y - v.vTexCoord0.y) < 0) && (lineFour.x > 0)) {
				checkVar += 1.f;
			}
			if ((((v.vTexCoord0.x * lineFour.x) + lineFour.y - v.vTexCoord0.y) < 0) && (lineFour.x < 0)) {
				checkVar += 1.f;
			}
			
			if (infGrad5 == 1) {
				if (v.vTexCoord0.x > lineFive.y) {
					checkVar += 1.f;
				}
			} else {
				if ((((v.vTexCoord0.x * lineFive.x) + lineFive.y - v.vTexCoord0.y) < 0) && (lineFive.x < 0)) {
					checkVar += 1.f;
				}
				if ((((v.vTexCoord0.x * lineFive.x) + lineFive.y - v.vTexCoord0.y) > 0) && (lineFive.x > 0)) {
					checkVar += 1.f;
				}
			}
			
			if (infGrad6 == 1) {
				if (v.vTexCoord0.x > lineSix.y) {
					checkVar += 1.f;
				}
			} else {
				if ((((v.vTexCoord0.x * lineSix.x) + lineSix.y - v.vTexCoord0.y) < 0) && (lineSix.x < 0)) {
					checkVar += 1.f;
				}
				if ((((v.vTexCoord0.x * lineSix.x) + lineSix.y - v.vTexCoord0.y) > 0) && (lineSix.x > 0)) {
					checkVar += 1.f;
				}
			}
			
			float circleRadius = 0.02f;
			float blurDist = 0.005f;
			float blurDiff = circleRadius - blurDist;
			float lineWidth = 0.01f;
			float lineBlurWidth = 0.005f;
			float lineBlurPos = lineWidth - lineBlurWidth;
			float4 circleColour = vFirstColor;
			circleColour.rgb *= 0.65;
			
			float l = 0.f;
			if (l1 < circleRadius) {
				l = l1;
			} else if (l2 < circleRadius) {
				l = l2;
			} else if (l3 < circleRadius) {
				l = l3;
			} else if (l4 < circleRadius) {
				l = l4;
			} else if (l5 < circleRadius) {
				l = l5;
			} else if (l6 < circleRadius) {
				l = l6;
			} else {
				l = circleRadius * 10.f;
			}
			
			if (checkVar == 6) {
				colour = vFirstColor;
			}
			
			float4 oldColour = colour;
			
			//if ((((v.vTexCoord0.x * lineOne.x) + lineOne.y - v.vTexCoord0.y) == 0) && v.vTexCoord0.x > pointOne.x && v.vTexCoord0.x < pointTwo.x) {
			//	colour = vFirstColor;
			//	colour.rgb *= 0.65f;
			//	if (absLineVal1 > lineBlurPos) {
			//		colour = lerp(oldColour, circleColour, (lineWidth - absLineVal1) / lineBlurWidth);
			//	}
			//}
			
			oldColour = colour;
			
			if ( l < circleRadius) {
				if (l < blurDiff) {
					colour = vFirstColor;
					colour.rgb *= 0.65;
				} else {
					colour = lerp(oldColour, circleColour, (circleRadius - l) / blurDist);
				}
			}
			
			return colour;
		}
		
	]]
}


BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}


Effect Color
{
	VertexShader = "VertexShader"
	PixelShader = "PixelColor"
}

Effect Texture
{
	VertexShader = "VertexShader"
	PixelShader = "PixelTexture"
}

