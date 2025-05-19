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
		    float value = floor((Offset.x) * 10.f) + 1.f;
			float commaVal = floor(value / 1000000.f);
			float endVal = floor(value / 1000.f) - (commaVal * 1000.f);
			float startVal = value - (endVal * 1000.f) - (commaVal * 1000000.f);
			float gap = (endVal - startVal);
			float dispVal = floor(startVal + gap * sin(vTime * 4.f));
			if (vTime > 0.375) {
				dispVal = endVal;
			}
			float hunDisp = floor(dispVal/100.f);
			float tenDisp = floor(dispVal/10.f) - hunDisp * 10.f;
			float oneDisp = dispVal - (hunDisp * 100.f) - (tenDisp * 10.f);
			float pointOne = 0.1f/3.f;
			float pointTwo = pointOne * 2.f;
			float4 OutColour;
			if(v.vTexCoord.x < pointOne && hunDisp > 0) {
				float xPoint = (0.1f * hunDisp) + v.vTexCoord.x;
				OutColour =  tex2D( MapTexture, float2(xPoint, v.vTexCoord.y));
			} else if(v.vTexCoord.x > pointOne && v.vTexCoord.x < pointTwo && (hunDisp > 0 || tenDisp > 0)) {
				float xPoint2 = (0.1f * tenDisp) + (v.vTexCoord.x - pointOne);
				OutColour =  tex2D( MapTexture, float2(xPoint2, v.vTexCoord.y));
			} else if(v.vTexCoord.x > pointTwo) {
				float xPoint3 = (0.1f * oneDisp) + (v.vTexCoord.x - pointTwo);
				OutColour =  tex2D( MapTexture, float2(xPoint3, v.vTexCoord.y));
			}
			else {
				return float4(0,0,0,0);
			}
			if(commaVal == 1) {
				if(OutColour.a > 0.5) {
					OutColour = float4(0.918,0.631,0.055,OutColour.a);
				}
			} else {
				if(OutColour.a > 0.5) {
					OutColour = float4(0.137,0.808,1,OutColour.a);
				}
			}
			if(OutColour.a <= 0.5) {
				return float4(0,0,0,0);
			}
			return OutColour;
		}
	]]

	MainCode PixelShaderDown
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
		    float4 OutColor = OutColor = tex2D( MapTexture, v.vTexCoord );
					
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
		    float value = floor((Offset.x) * 10.f) + 1.f;
			float commaVal = floor(value / 1000000.f);
			float endVal = floor(value / 1000.f) - (commaVal * 1000.f);
			float startVal = value - (endVal * 1000.f) - (commaVal * 1000000.f);
			float gap = (endVal - startVal);
			float dispVal = floor(startVal + gap * sin(vTime * 4.f));
			if (vTime > 0.375) {
				dispVal = endVal;
			}
			float hunDisp = floor(dispVal/100.f);
			float tenDisp = floor(dispVal/10.f) - hunDisp * 10.f;
			float oneDisp = dispVal - (hunDisp * 100.f) - (tenDisp * 10.f);
			float pointOne = 0.1f/3.f;
			float pointTwo = pointOne * 2.f;
			float4 OutColour;
			if(v.vTexCoord.x < pointOne && hunDisp > 0) {
				float xPoint = (0.1f * hunDisp) + v.vTexCoord.x;
				OutColour =  tex2D( MapTexture, float2(xPoint, v.vTexCoord.y));
			} else if(v.vTexCoord.x > pointOne && v.vTexCoord.x < pointTwo && (hunDisp > 0 || tenDisp > 0)) {
				float xPoint2 = (0.1f * tenDisp) + (v.vTexCoord.x - pointOne);
				OutColour =  tex2D( MapTexture, float2(xPoint2, v.vTexCoord.y));
			} else if(v.vTexCoord.x > pointTwo) {
				float xPoint3 = (0.1f * oneDisp) + (v.vTexCoord.x - pointTwo);
				OutColour =  tex2D( MapTexture, float2(xPoint3, v.vTexCoord.y));
			}
			else {
				return float4(0,0,0,0);
			}
			if(commaVal == 1) {
				if(OutColour.a > 0.5) {
					OutColour = float4(0.918,0.631,0.055,OutColour.a);
				}
			} else {
				if(OutColour.a > 0.5) {
					OutColour = float4(0.137,0.808,1,OutColour.a);
				}
			}
			if(OutColour.a <= 0.5) {
				return float4(0,0,0,0);
			}
			return OutColour;
		}	
	]]

	MainCode PixelShaderOver
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
		    float vTime = (Time - AnimationTime);
		    float value = floor((Offset.x) * 10.f) + 1.f;
			float endVal = floor(value / 1000.f);
			float startVal = value - (endVal * 1000.f);
			float gap = (endVal - startVal)/100.f;
			float yPos = 1.f -  (startVal/100.f);
			yPos += gap * sin(vTime);
			float timeCheck = saturate(vTime);
			if (startVal == 75) {
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