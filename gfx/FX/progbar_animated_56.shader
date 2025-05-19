Includes = {
	"buttonstate.fxh"
	"sprite_animation.fxh"
}

PixelShader =
{
	Samplers =
	{
		MapTexture =
		{
			Index = 0
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}


VertexStruct VS_OUTPUT
{
	float4  vPosition : PDX_POSITION;
	float2  vTexCoord : TEXCOORD0;
@ifdef ANIMATED
	float4  vAnimatedTexCoord : TEXCOORD1;
@endif
@ifdef MASKING
	float2  vMaskingTexCoord : TEXCOORD2;
@endif
};


VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main(const VS_INPUT v )
		{
		    VS_OUTPUT Out;
		    Out.vPosition  = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1 ) );
		
		    Out.vTexCoord = v.vTexCoord;
			
		#ifdef ANIMATED
			//Out.vAnimatedTexCoord = GetAnimatedTexcoord(v.vTexCoord);	
		#endif

		#ifdef MASKING
			A bit hacky, but we want the masking texture coordinates to be in the range [0,1]. We turn all 0's to 0 and all nonzero to 1.
			Out.vMaskingTexCoord = saturate(v.vTexCoord * 1000); 
		#endif
		
		    return Out;
		}
	]]
	
	MainCode VertexShader2
	[[
		VS_OUTPUT main(const VS_INPUT v )
		{
		    VS_OUTPUT Out;
		    Out.vPosition  = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1 ) );
		
		    Out.vTexCoord = v.vTexCoord;
			
		#ifdef ANIMATED
			//Out.vAnimatedTexCoord = GetAnimatedTexcoord(v.vTexCoord);	
		#endif

		#ifdef MASKING
			A bit hacky, but we want the masking texture coordinates to be in the range [0,1]. We turn all 0's to 0 and all nonzero to 1.
			Out.vMaskingTexCoord = saturate(v.vTexCoord * 1000); 
		#endif
		
		    return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelShaderUp
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
		    float vTime = (Time - AnimationTime);
		    float value = Offset.x + 1.f;
			float commaVal = floor(value / 1000000.f);
			float progVal = floor(value / 10000.f) - (commaVal * 100.f);
			float repVal = floor(value / 100.f) - (commaVal * 10000.f) - (progVal * 100.f);
			float natVal = value - (repVal * 100.f) - (progVal * 10000.f) - (commaVal * 1000000.f);
			float gap = (progVal - natVal)/100.f;
			float xPos = (natVal/100.f);
			xPos += gap * sin(vTime* 3.f);
			if(commaVal == 0) {
				if (vTime < 0.5) {
					if (v.vTexCoord.x > xPos) {
						return tex2D(MapTexture, float2(0.75 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.25 ,v.vTexCoord.y));
					}
				}
				else {
					if (v.vTexCoord.x > progVal/100.f) {
						return tex2D(MapTexture, float2(0.75 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.25 ,v.vTexCoord.y));
					}
				}
			}
			else {
				float LHSgap = progVal;
				float RHSgap1 = 100.f - repVal;
				float RHSgap2 = 100.f - natVal;
				float RHSgap3 = 100.f - progVal;
				LHSgap *= sin(vTime);
				RHSgap1 *= sin(vTime);
				RHSgap2 *= sin(vTime);
				RHSgap3 *= sin(vTime);
				float LHSpos = LHSgap;
				float RHSpos1 = 100.f - RHSgap1;
				float RHSpos2 = 100.f - RHSgap2;
				float RHSpos3 = 100.f - RHSgap3;
				if (vTime < 1.5) {
					if (v.vTexCoord.x > RHSpos2/100.f) {
						return tex2D(MapTexture, float2(0.8 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x < LHSpos/100.f) {
						return tex2D(MapTexture, float2(0.1 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > RHSpos3/100.f && v.vTexCoord.x < RHSpos1/100.f) {
						return tex2D(MapTexture, float2(0.3 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > RHSpos1/100.f && v.vTexCoord.x < RHSpos2/100.f) {
						return tex2D(MapTexture, float2(0.6 ,v.vTexCoord.y));
					}
					else{
						return float4(0,0,0,0);
					}
				}
				else {
					if (v.vTexCoord.x < progVal/100.f) {
						return tex2D(MapTexture, float2(0.1 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > natVal/100.f) {
						return tex2D(MapTexture, float2(0.8 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x < natVal/100.f & v.vTexCoord.x > repVal/100.f) {
						return tex2D(MapTexture, float2(0.6 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.4 ,v.vTexCoord.y));
					}
				}
			}
		}
	]]

	MainCode PixelShaderDown
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
		    float4 OutColor = tex2D( MapTexture, v.vTexCoord );
					
		#ifdef ANIMATED
			OutColor = Animate(OutColor, v.vTexCoord, v.MapTexture, MapTexture, MapTexture, MapTexture, MapTexture);
		#endif

		#ifdef MASKING
			float4 MaskColor = tex2D( MaskingTexture, v.vTexCoord );
			OutColor.a *= MaskColor.a;
		#endif
			
			OutColor *= Color;

			return OutColor;
		}
	]]

	MainCode PixelShaderDisable
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float vTime = (Time - AnimationTime);
		    float value = Offset.x + 1.f;
			float commaVal = floor(value / 1000000.f);
			float progVal = floor(value / 10000.f) - (commaVal * 100.f);
			float repVal = floor(value / 100.f) - (commaVal * 10000.f) - (progVal * 100.f);
			float natVal = value - (repVal * 100.f) - (progVal * 10000.f) - (commaVal * 1000000.f);
			float gap = (progVal - natVal)/100.f;
			float xPos = (natVal/100.f);
			xPos += gap * sin(vTime* 3.f);
			if(commaVal == 0) {
				if (vTime < 0.5) {
					if (v.vTexCoord.x > xPos) {
						return tex2D(MapTexture, float2(0.75 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.25 ,v.vTexCoord.y));
					}
				}
				else {
					if (v.vTexCoord.x > progVal/100.f) {
						return tex2D(MapTexture, float2(0.75 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.25 ,v.vTexCoord.y));
					}
				}
			}
			else {
				float LHSgap = progVal;
				float RHSgap1 = 100.f - repVal;
				float RHSgap2 = 100.f - natVal;
				float RHSgap3 = 100.f - progVal;
				LHSgap *= sin(vTime);
				RHSgap1 *= sin(vTime);
				RHSgap2 *= sin(vTime);
				RHSgap3 *= sin(vTime);
				float LHSpos = LHSgap;
				float RHSpos1 = 100.f - RHSgap1;
				float RHSpos2 = 100.f - RHSgap2;
				float RHSpos3 = 100.f - RHSgap3;
				if (vTime < 1.5) {
					if (v.vTexCoord.x > RHSpos2/100.f) {
						return tex2D(MapTexture, float2(0.8 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x < LHSpos/100.f) {
						return tex2D(MapTexture, float2(0.1 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > RHSpos3/100.f && v.vTexCoord.x < RHSpos1/100.f) {
						return tex2D(MapTexture, float2(0.3 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > RHSpos1/100.f && v.vTexCoord.x < RHSpos2/100.f) {
						return tex2D(MapTexture, float2(0.6 ,v.vTexCoord.y));
					}
					else{
						return float4(0,0,0,0);
					}
				}
				else {
					if (v.vTexCoord.x < progVal/100.f) {
						return tex2D(MapTexture, float2(0.1 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x > natVal/100.f) {
						return tex2D(MapTexture, float2(0.8 ,v.vTexCoord.y));
					}
					else if(v.vTexCoord.x < natVal/100.f & v.vTexCoord.x > repVal/100.f) {
						return tex2D(MapTexture, float2(0.6 ,v.vTexCoord.y));
					}
					else {
						return tex2D(MapTexture, float2(0.4 ,v.vTexCoord.y));
					}
				}
			}
		}	
	]]

	MainCode PixelShaderOver
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
		    float vTime = (Time - AnimationTime);
		    float value = Offset.x + 1.f;
			float endVal = floor(value / 1000.f);
			float startVal = value - (endVal * 1000.f);
			float gap = (endVal - startVal)/100.f;
			float yPos = 1.f -  (startVal/100.f);
			yPos += gap * sin(vTime);
			float timeCheck = saturate(vTime);
			if (startVal == 5) {
				return float4(1,0,1,1);
			}
			else {
				return float4(1,1,1,1);
			}
		}
	]]

}


BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}


Effect Up
{
	VertexShader = "VertexShader2"
	PixelShader = "PixelShaderUp"
}

Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderDown"
}

Effect Disable
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderDisable"
}

Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderOver"
}