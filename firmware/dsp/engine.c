/* Portable reference DSP, shared by the browser WASM and native tests.
 * This is not ESP-IDF firmware and does not configure PARLIO/DMA.
 * Causal semantics: all modulation sources read previous ACTIVE pixel,
 * simultaneously; history resets at each field. V phase is per column.
 */
#include "engine.h"
#include "sine_table.h"
typedef struct { float frequency,fine,phase,morph; int mixed; } Osc;
typedef struct { int mode; float volts,frequency,amplitude; } CV;
static Osc osc[6];static CV cv[2];
static uint8_t matrix[8][18],active_src[18][8],src_count[18];
static int count=0,width=VS_WIDTH,height=VS_HEIGHT;
static float vphase[3][VS_WIDTH];
static uint8_t pixels[VS_WIDTH*VS_HEIGHT*4],luma[VS_WIDTH*VS_HEIGHT];
static float clampf(float x,float lo,float hi){return x<lo?lo:x>hi?hi:x;}
static float absf(float x){return x<0?-x:x;}
static float fract(float x){float y=x-(int)x;return y<0?y+1:y;}
static float sine(float x){float p=fract(x)*1024;int i=(int)p;return sine_table[i]+(sine_table[i+1]-sine_table[i])*(p-i);}
static float blep(float t,float dt){
 if(dt<1e-9f)return 0;
 if(t<dt){float a=t/dt;return 2*a-a*a-1;}
 if(t>1-dt){float a=(t-1)/dt;return a*a+2*a+1;}
 return 0;
}
static float triangle(float p){return 1-4*absf(fract(p+.25f)-.5f);}
static float saw(float p,float dt){return 2*p-1-blep(p,dt);}
static float square(float p,float dt){return (p<.5f?1.f:-1.f)+blep(p,dt)-blep(fract(p+.5f),dt);}
static float wave(float p,float morph,float dt){
 p=fract(p);int a=(int)morph;float f=morph-a,lo,hi;
 switch(a){
  case 0:lo=sine(p);if(f==0)return lo;hi=triangle(p);break;
  case 1:lo=triangle(p);if(f==0)return lo;hi=saw(p,dt);break;
  case 2:lo=saw(p,dt);if(f==0)return lo;hi=square(p,dt);break;
  default:return square(p,dt);
 }
 return lo+f*(hi-lo);
}
static void compile_routes(void){
 for(int d=0;d<18;d++){src_count[d]=0;for(int s=0;s<8;s++)if(matrix[s][d])active_src[d][src_count[d]++]=(uint8_t)s;}
}
void clear_routes(void){for(int s=0;s<8;s++)for(int d=0;d<18;d++)matrix[s][d]=0;count=0;compile_routes();}
int set_route(int s,int d,int on){
 if(s<0||s>=8||d<0||d>=18)return -1;
 on=!!on;
 if(matrix[s][d]==on)return 0;
 if(on&&count>=VS_MAX_ROUTES)return -2;
 matrix[s][d]=(uint8_t)on;count+=on?1:-1;compile_routes();return 0;
}
int route_count(void){return count;}
int set_osc(int i,float frequency,float fine,float phase,float morph,int mixed){
 if(i<0||i>=6||!(frequency>=.25f&&frequency<=64)||!(fine>=-1&&fine<=1)||!(phase>=0&&phase<=1)||!(morph>=0&&morph<=3))return -1;
 osc[i]=(Osc){frequency,fine,phase,morph,!!mixed};return 0;
}
int set_cv(int i,int mode,float volts,float frequency,float amplitude){
 if(i<0||i>=2||mode<0||mode>1||!(volts>=-15&&volts<=15)||!(frequency>=0&&frequency<=100)||!(amplitude>=0&&amplitude<=10))return -1;
 cv[i]=(CV){mode,volts,frequency,amplitude};return 0;
}
int set_size(int w,int h){if(w<16||w>720||h<16||h>480||(h&1))return -1;width=w;height=h;return 0;}
int get_width(void){return width;}int get_height(void){return height;}
uint8_t *pixels_ptr(void){return pixels;}uint8_t *luma_ptr(void){return luma;}
float cv_adc_voltage(float v){
 /* DC model ONLY: OPA2197 ideal output clipped to rails, Rload 100k,
  * Rfilter 4.7k. Does not certify clamp or powered-off behavior. */
 float out=clampf(1.65f-.12f*v,0,5)*100000.f/104700.f;
 out=clampf(out,0,3.3f);int code=(int)(out*4095.f/3.3f+.5f);return code*3.3f/4095.f;
}
float cv_decode(float adc){return clampf((1.65f-adc*1.047f)/1.2f,-1,1);}
static float cv_source(int i,double t){
 CV *c=&cv[i];float volts=c->volts;
 if(c->mode){
  /* Ideal two-pole response, including ADC load on second pole.
   * Phase lag supplied using small-angle atan approximation, sufficient
   * only in specified 0..100 Hz band; amplitude uses sqrt approximation. */
  float a=c->frequency/282.1898f,b=c->frequency/354.546f;
  float atten=1.f/((1+.5f*a*a-.125f*a*a*a*a)*(1+.5f*b*b-.125f*b*b*b*b));
  float lag=(a-a*a*a/3+b-b*b*b/3)/6.28318530718f;
  volts+=c->amplitude*atten*sine((float)(t*c->frequency-(int64_t)(t*c->frequency))-lag);
 }
 return cv_decode(cv_adc_voltage(clampf(volts,-15,15)));
}
void reset_state(void){
 clear_routes();width=720;height=480;
 for(int i=0;i<6;i++)osc[i]=(Osc){8.f+4.f*(i%3),0,0,0,i==0||i==3};
 for(int i=0;i<2;i++)cv[i]=(CV){0,0,1,5};
}
int render_frame(double time_seconds){
 if(!(time_seconds>=0&&time_seconds<1e8))return -1;
 int nmix=0;for(int i=0;i<6;i++)nmix+=osc[i].mixed;
 float base[6],base_dt[6];float inv_mix=nmix?1.f/nmix:0;
 for(int i=0;i<6;i++){base[i]=clampf(osc[i].frequency+osc[i].fine,.01f,64.f);base_dt[i]=base[i]/(i<3?width:height);}
 for(int field=0;field<2;field++){
  float prev[8]={0};int64_t last_cv_tick=-1;
  for(int i=0;i<3;i++)for(int x=0;x<width;x++)vphase[i][x]=(float)field*base[i+3]/height;
  for(int y=field;y<height;y+=2){
   float hp[3]={0};
   for(int x=0;x<width;x++){
    /* 4 kSPS sample-and-hold, with true 525-line field ordering.
     * Reduced sizes are only test modes; UI always asks for 720x480. */
    double half_start=field?570:44;
    double seconds=time_seconds+(half_start+(y-field)*480./height)*858./27000000.+(244.+x*1440./width)/27000000.;
    int64_t tick=(int64_t)(seconds*4000.);
    if(tick!=last_cv_tick){double sampled=tick/4000.;prev[6]=cv_source(0,sampled);prev[7]=cv_source(1,sampled);last_cv_tick=tick;}
    float out[6],mix=0;
    for(int i=0;i<6;i++){
     float sums[3]={0};for(int m=0;m<3;m++){
      int d=i*3+m;for(int k=0;k<src_count[d];k++)sums[m]+=prev[active_src[d][k]];
      sums[m]=clampf(sums[m],-4,4);
     }
     float dt=base_dt[i]*clampf(1+.25f*sums[0],0,2);
     float phase=i<3?hp[i]:vphase[i-3][x];
     out[i]=clampf(wave(phase+osc[i].phase+.125f*sums[2],osc[i].morph,dt)*clampf(1+.25f*sums[1],0,2),-1,1);
     if(osc[i].mixed)mix+=(out[i]+1)*.5f;
     if(i<3)hp[i]=fract(hp[i]+dt);else vphase[i-3][x]=fract(vphase[i-3][x]+2*dt);
    }
    for(int i=0;i<6;i++)prev[i]=out[i];
    int k=y*width+x;uint8_t val=nmix?(uint8_t)(clampf(mix*inv_mix,0,1)*255+.5f):0;luma[k]=val;
    pixels[k*4]=pixels[k*4+1]=pixels[k*4+2]=val;pixels[k*4+3]=255;
   }
  }
 }
 return width*height;
}
