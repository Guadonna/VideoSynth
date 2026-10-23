#include "../firmware/dsp/engine.h"
#include <assert.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
int main(void){
 reset_state();assert(get_width()==720&&get_height()==480);
 for(int i=0;i<6;i++)assert(set_osc(i,8,0,0,0,0)==0);
 assert(render_frame(0)==345600);for(int i=0;i<345600;i++)assert(luma_ptr()[i]==0);
 assert(cv_adc_voltage(10)>.429&&cv_adc_voltage(10)<.431);
 assert(cv_adc_voltage(-10)>2.721&&cv_adc_voltage(-10)<2.723);
 reset_state();for(int s=0;s<6;s++)for(int d=0;d<6;d++)assert(set_route(s,d*3+(s+d)%3,1)==0);
 assert(route_count()==36&&set_route(7,17,1)==-2);
 struct timespec a,b;clock_gettime(CLOCK_MONOTONIC,&a);for(int i=0;i<20;i++)assert(render_frame(i*1001./30000)==345600);clock_gettime(CLOCK_MONOTONIC,&b);
 double ms=((b.tv_sec-a.tv_sec)*1000.+(b.tv_nsec-a.tv_nsec)/1e6)/20;
 uint32_t hash=2166136261u;for(int i=0;i<345600;i++)hash=(hash^luma_ptr()[i])*16777619u;
 printf("{\"host_native_tests\":\"PASS\",\"stress_frames\":20,\"average_render_ms\":%.4f,\"checksum\":%u,\"scope\":\"host CPU, not ESP32-P4\"}\n",ms,hash);return 0;
}
