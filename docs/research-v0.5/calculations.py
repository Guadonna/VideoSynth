"""v0.5 arithmetic only: no MCU benchmark, analog simulation or physical test.
Run with Python 3; outputs are written next to this file.
"""
from pathlib import Path
from fractions import Fraction
import csv
import json
import math

OUT = Path(__file__).resolve().parent
FPS = Fraction(30000, 1001)
WIDTH, HEIGHT = 720, 480
POINTS = WIDTH * HEIGHT * FPS


def write_csv(name, rows):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


video = []
for bits in (8, 16):
    stride = bits // 8
    video.append(dict(storage_bits_per_point=bits, width=WIDTH, height=HEIGHT,
                      frames_s=float(FPS), field_rate_Hz=float(2*FPS),
                      active_points_s=float(POINTS), frame_bytes=WIDTH*HEIGHT*stride,
                      double_frame_bytes=2*WIDTH*HEIGHT*stride,
                      active_MB_s=float(POINTS*stride/1000000),
                      full_raster_13M5_MB_s=13.5*stride,
                      full_raster_27M_MB_s=27*stride,
                      sixteen_lines_13M5_bytes=16*858*stride,
                      note='16-bit storage can carry >8 DAC bits; does not mean 16-bit analog accuracy'))
write_csv('video-budget.csv', video)

cpus = {'RP2350_150_one_core':150e6, 'RP2350_150_two_cores_ideal':300e6,
        'RP2350_135_two_cores_ideal':270e6, 'ESP32S3_240_two_cores_ideal':480e6,
        'ESP32P4_400_one_core':400e6, 'ESP32P4_400_two_cores_ideal':800e6,
        'STM32H743_480_one_core':480e6, 'RT1176_M7_996_one_core':996e6}
write_csv('cpu-budget.csv', [dict(cpu=k, cycles_per_point=float(v/POINTS),
    cycles_per_point_with_40pct_reserve=float(v*.6/POINTS),
    warning='Ideal capacity, not measured; feedback may prevent multicore/SIMD scaling') for k,v in cpus.items()])

write_csv('dsp-sensitivity.csv', [dict(assumed_cycles_per_point=c,
    required_Mcycles_s=float(POINTS*c/1000000),
    ideal_P4_2core_with_40pct_reserve_max_fps=800e6*.6/(WIDTH*HEIGHT*c),
    warning='Assumed cost only, not measured, not a prediction') for c in (24,40,60,100,160)])

write_csv('power-budget.csv',[dict(assumed_load_W=w, assumed_efficiency=.90,
    plus12_current_A=w/(12*.9), conversion_loss_W=w*(1/.9-1),
    note='All modeled load supplied from +12 V; any -12 V analog load must be budgeted separately') for w in (2,3.5,5)])

# Illustrative anti-alias filter, not a designed circuit.
write_csv('cv-filter-sensitivity.csv',[dict(frequency_Hz=f, order=4,
    assumed_corner_Hz=250, attenuation_dB=10*math.log10(1+(f/250)**8),
    note='Ideal fourth-order Butterworth only; tolerances, noise and settling not modeled') for f in (100,250,2000)])

with (OUT/'components-preliminary.csv').open(encoding='utf-8-sig',newline='') as f:
    bom=list(csv.DictReader(f))
summary={
    'nature':'Arithmetic with explicit assumptions; no hardware benchmark',
    'confirmed_mode':'720x480, 525 total lines, 30000/1001 frames/s, 60000/1001 fields/s',
    'horizontal_Hz':float(FPS*525),
    'line_us':float(1e6/(FPS*525)),
    'samples_per_line_at_13M5':858,
    'samples_per_half_line_at_13M5':429,
    'samples_per_frame_at_13M5':858*525,
    'samples_per_field_at_13M5':str(Fraction(858*525,2)),
    'samples_per_field_at_27M':1716*525//2,
    'active_points_s':float(POINTS),
    'six_oscillator_evaluations_s_upper_model':float(POINTS*6),
    'ratio_to_old_360x288_at_50_common_points':float(POINTS/(360*288*50)),
    'max_enabled_routes_total':36,
    'matrix_cells':8*18,
    'max_OSC_route_contributions_s':float(POINTS*36),
    'fixed_strength_note':'For equal per-type weights, sum sources then scale per destination; route contributions need not be MACs',
    'max_destination_scalings_s_upper_bound':float(POINTS*18),
    'all_CV_routes_at_4kHz_additions_s':36*4000,
    'CV_sampling_per_channel_Hz_assumption':4000,
    'pot_rate_per_control_Hz_assumption':100,
    'ADC_total_samples_s_with_pot_discard':2*4000+24*100*2,
    'ADC_SPI_1MHz_24bits_bus_fraction':(2*4000+24*100*2)*24/1e6,
    'CV_adjacent_sample_skew_us_assumption':24,
    'CV_phase_error_at100Hz_for24us_degrees':360*100*24e-6,
    'nominal_CV_LSB_V_with_3V3_ref_and_0V12_per_V_gain':3.3/4096/.12,
    'continuous_link_8bits_20MHz_raw_MB_s':20,
    'P4_nominal_GPIO_with_DAC_clock_and_service_USB':12+6+4+4+8+4+6+2,
    'preview_320x240_RGB565_15fps_MB_s':320*240*2*15/1e6,
    'pixel_link_13M5_8bit_bus_fraction_at20MHz':13.5/20,
    'RP2350_520KiB_minus_one_8bit_frame_bytes':520*1024-720*480,
    'P4_one_core_40pct_reserve_cycles_per_point':float(400e6*.6/POINTS),
    'P4_two_cores_40pct_reserve_cycles_per_point_ideal':float(800e6*.6/POINTS),
    'feedback_previous_frame_6x16bit_double_bytes':6*720*480*2*2,
    'feedback_previous_frame_6x16bit_read_plus_write_MB_s':float(POINTS*6*2*2/1000000),
    'BOM_electronics_USD_low':round(sum(float(r['line_USD_low']) for r in bom),2),
    'BOM_electronics_USD_high':round(sum(float(r['line_USD_high']) for r in bom),2),
}
assert Fraction(13500000,858*525)==FPS
assert Fraction(13500000,1)/(FPS*2)==Fraction(450450,2)
assert summary['matrix_cells']==144 and summary['max_enabled_routes_total']==36
assert 720*480 < 520*1024 < 2*720*480
(OUT/'calculation-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
