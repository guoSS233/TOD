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
			float2 vDiff = 0.5f - v.vTexCoord0;
			float vAngle = atan2( vDiff.x, vDiff.y ) + 3.14159265f;

			float2 vDiff2 = 0.5f - v.vTexCoord0 - float2(0/400.f, 1/400.f);
			float vAngle2 = atan2( vDiff2.x, vDiff2.y ) + 3.14159265f;
			float vLerp2 = ( vAngle2 - CurrentState* 3.14159265f * 2.f);

			float2 vDiff3 = 0.5f - v.vTexCoord0 - float2(0/400.f, -1/400.f);
			float vAngle3 = atan2( vDiff3.x, vDiff3.y ) + 3.14159265f;
			float vLerp3 = ( vAngle3 - CurrentState* 3.14159265f * 2.f);

			float2 vDiff4 = 0.5f - v.vTexCoord0 - float2(1/400.f, 0/400.f);
			float vAngle4 = atan2( vDiff4.x, vDiff4.y ) + 3.14159265f;
			float vLerp4 = ( vAngle4 - CurrentState* 3.14159265f * 2.f);

			float2 vDiff5 = 0.5f - v.vTexCoord0 - float2(-1/400.f, 0/400.f);
			float vAngle5 = atan2( vDiff5.x, vDiff5.y ) + 3.14159265f;
			float vLerp5 = ( vAngle5 - CurrentState* 3.14159265f * 2.f);

			float vLerp = ( vAngle - CurrentState* 3.14159265f * 2.f);
			if (vLerp >= 0.f && (vLerp2 <= 0.f || vLerp3 <= 0.f || vLerp4 <= 0.f || vLerp5 <= 0.f)) {
				return float4(0, 0, 0, 1);
			} else if (vLerp > 0.f) {
				return tex2D( TextureTwo, float2(v.vTexCoord0.x, -v.vTexCoord0.y) );
			} else {
				return tex2D( TextureOne, float2(v.vTexCoord0.x, -v.vTexCoord0.y) );
			}
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

