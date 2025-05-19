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
			Out.vTexCoord0  = v.vTexCoord;
		
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
			float value = CurrentState * 100000.f;
			float end = mod(value, 1000.f) / 100.f;
			float start = floor(value / 1000.f) / 100.f;

			float2 vDiff = 0.5f - v.vTexCoord0;
			float vAngle = (atan2( vDiff.x, vDiff.y ) + 3.14159265f);

			float sAngle = start * (2 * 3.14159265f);
			float eAngle = end * (2 * 3.14159265f);

			// Midpoint angle between start and end
			float mAngle = (sAngle + eAngle) / 2.f;

			// Ratio of the icon size to the entire image size
			float ratio = 1.0f;

			// Compute location of the top-left corner of the icon
			float2 iconTopLeft = float2(0.5f, 0.5f) + 0.21 * float2(sin(mAngle), cos(mAngle)) + (1/ratio) * float2(-0.5f, -0.5f) ;
			// Compute the position in the icon texture associated with the current pixel
			float2 imgPos = (v.vTexCoord0 - iconTopLeft) * ratio;

			// If outside of the slice defined by start/end, return empty texture
			if (vAngle < sAngle || vAngle > eAngle + 0.01f) {
				return float4(0, 0, 0, 0);
			}
			
			float4 colourOne = tex2D( TextureOne, v.vTexCoord0.xy );
			float4 colourTwo = float4(0,0,0,0);
			
			float2 vPos = float2(v.vTexCoord0.x - 0.5f, 0.5f - v.vTexCoord0.y);
			float l = length(vPos);
			float2 comparison = l * float2(sin(eAngle), -cos(eAngle));
			float2 comparison2 = l * float2(-sin(eAngle), cos(eAngle));
			float d = length(comparison - vPos);
			float d2 = length(comparison2 - vPos);
			float blurDist = 0.01f;
			
			float4 vOne = vFirstColor;
			float4 vTwo = vSecondColor;
			
			vOne.a = 1.0f;

			float4 colour = tex2D( TextureOne, v.vTexCoord0.xy );

			// If imgPos is actually within the icon, overlay icon
			if (imgPos.x > 0 && imgPos.x < 1 && imgPos.y > 0 && imgPos.y < 1) {
				float4 mask = tex2D( TextureTwo, float2(imgPos.x, -imgPos.y) );
				if (mask.a > 0) {
					colour.rgb *= 0.65;
				}
			}
			
			if (d < blurDist) {
				if (eAngle > vAngle) {
					colour = lerp(vTwo, vOne, (d + blurDist) / (blurDist * 2.f));
				} else {
					colour = lerp(vOne, vTwo, (d + blurDist) / (blurDist * 2.f));
				}
			}
			
			if (l > 0.506f) {
				return float4 (0,0,0,0);
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

