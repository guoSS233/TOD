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
			Out.vTexCoord0.y = 1.f-Out.vTexCoord0.y;

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
			float2 vDiff = float2(0.5f, 0.982f) - v.vTexCoord0;
			float vAngle = atan2( vDiff.x, vDiff.y ) + 3.14159265f;

			float value = CurrentState * 100000.f;
			float start = floor((value / 1000.f) + 0.5) / 100.f;
			float end = mod(value, 1000.f) / 100.f;

			
			float vLerp = saturate( ( vAngle - (end + 0.5f)* 3.14159265f * 1.f) * 50.f );
			float4 vOne = vFirstColor;
			float4 vTwo = vSecondColor;

			vOne.a = 1.0f;

			float pAngle = ((1.5f - end)* 3.14159265f * 1.f);

			float blurDist = 0.10f;

			float2 vPos = float2(v.vTexCoord0.x - 0.5f, 0.982f - v.vTexCoord0.y);
			float l = length(vPos);
			float2 comparison = l * float2(sin(pAngle), -cos(pAngle));
			float2 comparison2 = l * float2(-sin(pAngle), cos(pAngle));

			float midway = (end - start) * 0.5f + start;
			float lhsMidpointAngle = 3.14159265f * (0.48f + midway);
			float2 lhsMidpoint = 0.335f * float2(-sin(lhsMidpointAngle), -cos(lhsMidpointAngle));
			float2 lhsImgPos = (lhsMidpoint - vPos) * 3.2f + float2(0.5f, 0.5f);

			float rhsMidpointAngle = 3.14159265f * (1.5f - (end * 0.5f));
			float2 rhsMidpoint = 0.335f * float2(-cos(rhsMidpointAngle), -sin(rhsMidpointAngle));
			float2 rhsImgPos = (rhsMidpoint - vPos) * 3.2f + float2(0.5f, 0.5f);

			
			float4 color = float4(0,0,0,0);
			
			float d = length(comparison - vPos);
			float d2 = length(comparison2 - vPos);
			if (d2 < d) {
				//d = d2;
			}

			if (end > start + 0.01f && lhsImgPos.x >= 0.0f && lhsImgPos.x <= 1.0f && lhsImgPos.y >= 0.0f
				&& lhsImgPos.y <= 1.0f && tex2D( TextureOne, float2(1.f - lhsImgPos.x, lhsImgPos.y) ).a > 0) {
				vOne.rgb = vOne.rgb * 0.65;
			}
			if (end < 1 && rhsImgPos.x >= 0.0f && rhsImgPos.x <= 1.0f && rhsImgPos.y >= 0.0f
				&& rhsImgPos.y <= 1.0f && tex2D( TextureTwo,  float2(1.f - rhsImgPos.x, rhsImgPos.y) ).a > 0) {
				vTwo.rgb = vTwo.rgb * 0.65;
			}
	

			if (d < blurDist) {
				if (pAngle > vAngle) {
					color = lerp(vOne, vTwo, (d + blurDist) / (blurDist * 2.f));
				} else {
					color = lerp(vTwo, vOne, (d + blurDist) / (blurDist * 2.f));
				}
			}
			else if (pAngle > vAngle) {
				color = vTwo;
			}
			else {
				color = vOne;
			}

			if (l > 0.5f) {
				return float4(0,0,0,0);
			}
			if (l < 0.17f) {
				return float4(0,0,0,0);
			}


			return color;

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

