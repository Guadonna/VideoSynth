#ifndef VIDEOSYNTH_ENGINE_H
#define VIDEOSYNTH_ENGINE_H
#include <stdint.h>
#define VS_WIDTH 720
#define VS_HEIGHT 480
#define VS_MAX_ROUTES 36
void reset_state(void);
int set_osc(int i, float frequency, float fine, float phase, float morph, int mixed);
int set_route(int source, int destination, int enabled);
int route_count(void);
void clear_routes(void);
int set_cv(int i, int mode, float volts, float frequency, float amplitude);
int render_frame(double time_seconds);
uint8_t *pixels_ptr(void);
uint8_t *luma_ptr(void);
int set_size(int width,int height);
int get_width(void);
int get_height(void);
float cv_adc_voltage(float input);
float cv_decode(float adc);
#endif
