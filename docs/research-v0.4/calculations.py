"""Feasibility arithmetic and topology model; not firmware or a hardware benchmark.

Run with Python 3 from any directory. Outputs are written beside this script.
CPU costs, utilisation allowance, power and efficiency are explicit assumptions.
"""
from pathlib import Path
import csv
import json
import math
from itertools import product

OUT = Path(__file__).resolve().parent
MODES = [(256, 240, 25), (360, 288, 25), (360, 288, 50), (720, 576, 25)]
CPUS = {"RP2350_150_1core": 150e6, "RP2350_150_2cores_upper_bound": 300e6,
        "RP2350_135_2cores_upper_bound": 270e6,
        "ESP32S3_240_2cores_upper_bound": 480e6,
        "ESP32P4_360_2cores_upper_bound": 720e6,
        "ESP32P4_400_1core": 400e6,
        "ESP32P4_400_2cores_upper_bound": 800e6,
        "STM32H743_480_1core": 480e6, "RT1176_M7_996_1core": 996e6}


def csv_write(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


rows, budgets, dsp = [], [], []
for w, h, fps in MODES:
    n = w * h * fps
    mode = f"{w}x{h}@{fps}"
    rows.append(dict(mode=mode, common_pixels_s=n, oscillator_evaluations_s=6*n,
                     frame_3x8_bytes=w*h*3, double_frame_3x8_bytes=w*h*6,
                     frame_padded32_bytes=w*h*4, double_frame_padded32_bytes=w*h*8,
                     transport_packed_MB_s=n*3/1e6, transport_padded_MB_s=n*4/1e6))
    for cpu, hz in CPUS.items():
        budgets.append(dict(mode=mode, cpu=cpu, cycles_per_common_pixel=hz/n,
                            cycles_with_40pct_reserve=0.60*hz/n))
    for edges in (0, 18, 54, 108):
        cost = 120 + 4*edges  # Illustrative scalar cost, NOT measured.
        dsp.append(dict(mode=mode, per_pixel_osc_edges=edges,
                        assumed_cycles_per_pixel=cost,
                        required_Mcycles_s=n*cost/1e6,
                        fraction_P4_two_400MHz_ideal=n*cost/800e6))
csv_write("video-memory.csv", rows)
csv_write("cpu-budgets.csv", budgets)
csv_write("dsp-sensitivity.csv", dsp)


def connected_components(edges, vertices):
    parent = {v: v for v in vertices}
    def root(v):
        while parent[v] != v:
            v = parent[v]
        return v
    for a, b in edges:
        parent[root(a)] = root(b)
    return {v: root(v) for v in vertices}


vertices = ["A", "B", "OUT1", "OUT2"]
g = connected_components([("A", "OUT1"), ("A", "OUT2"), ("B", "OUT1")], vertices)
assert g["B"] == g["OUT2"]  # Electrical equivalence invents a fourth route.
vertices = [f"{side}{i}" for i in range(9) for side in ("S", "D")]
for state in product((False, True), repeat=9):
    g = connected_components([(f"S{i}", f"D{i}") for i in range(9) if state[i]], vertices)
    measured = tuple(g[f"S{i}"] == g[f"D{i}"] for i in range(9))
    assert measured == state

electrical = []
for r in (4700, 22000, 47000):
    # N total contacts, each inactive contact has one series resistor plus pull-down.
    n, pull, source = 44, 1e6, 3.3
    sensed = source * pull / (pull + n*r)
    electrical.append(dict(series_ohm=r, group_contacts=n, pulldown_ohm=pull,
                           ideal_sensed_high_V=sensed,
                           MCP23S17_VIH_min_at_3V3=0.8*3.3,
                           ideal_margin_to_MCP23S17_VIH_V=sensed-0.8*3.3,
                           fault_current_to_zero_mA=15/r*1000,
                           fault_resistor_mW=15*15/r*1000,
                           current_44_clamped_contacts_mA=44*15/r*1000,
                           five_tau_for_2nF_us=5*r*2e-9*1e6))
csv_write("patch-electrical-assumptions.csv", electrical)

power = []
for watts in (3.0, 4.5, 6.0):
    power.append(dict(load_W=watts, assumed_efficiency=0.90,
                      USB_current_A=watts/(5*0.90),
                      eurorack_plus12_current_A=watts/(12*0.90),
                      converter_loss_W=watts*(1/0.90-1)))
csv_write("power-budget.csv", power)

# Ideal filter comparison: THS7314 is modified Butterworth, not exactly this model.
filters = []
for sample_mhz in (13.5, 27.0):
    for signal_mhz in (3.0, 5.0):
        image_mhz = sample_mhz - signal_mhz
        filters.append(dict(DAC_sample_MHz=sample_mhz, signal_MHz=signal_mhz,
                            first_image_MHz=image_mhz,
                            assumed_fifth_order_corner_MHz=8.5,
                            ideal_filter_image_attenuation_dB=10*math.log10(1+(image_mhz/8.5)**10),
                            caveat="Ideal filter only; 27 MSPS requires interpolation, not sample repetition"))
csv_write("video-filter-sensitivity.csv", filters)

with (OUT / "components-preliminary.csv").open(encoding="utf-8-sig", newline="") as f:
    bom = list(csv.DictReader(f))
bom_totals = {side: sum(float(r[f"line_USD_{side}"]) for r in bom) for side in ("low", "high")}
summary = {
    "nature": "Arithmetic and ideal connectivity models only; no physical measurements",
    "common_raster_samples_s": 864*625*25,
    "raster_packed24_MB_s": 864*625*25*3/1e6,
    "raster_padded32_MB_s": 864*625*25*4/1e6,
    "one_line_padded32_bytes": 864*4,
    "16_line_padded32_bytes": 16*864*4,
    "raster_field_samples": 864*625//2,
    "SPI_40MHz_320x240_RGB565_20fps_occupancy": 320*240*2*20/(40e6/8),
    "SPI_40MHz_240x240_RGB565_15fps_occupancy": 240*240*2*15/(40e6/8),
    "link_16bit_20MHz_MB_s": 16*20e6/8/1e6,
    "GPIO_RP_R2R_video_link_budget": 24+2+16+2+1,
    "GPIO_RP_clocked_DAC_video_link_budget": 24+2+16+2+1+1,
    "parallel_108_edges_360x288_50_MAC_s": 108*360*288*50,
    "CV36_edges_50ksps_MAC_s": 36*50000,
    "topology_unintended_route_demonstrated": True,
    "isolated_mixer_pair_states_verified": 512,
    "fault_clamps": "15/R assumes clamping near 0 V; not component qualification",
    "biased_scan_ideal_high_V": 0.3+(2.7-0.3)*2.2e6/(2.2e6+44*47000),
    "biased_scan_ideal_margin_to_0V9_threshold_V": 0.3+(2.7-0.3)*2.2e6/(2.2e6+44*47000)-0.9,
    "MCP23S17_guaranteed_VIH_3V3": 0.8*3.3,
    "raster_27MSPS_padded32_MB_s": 27e6*4/1e6,
    "16_line_27MSPS_padded32_bytes": 16*1728*4,
    "PAL_colour_line_frequency_table_tolerance_ppm": 0.00002*1e4,
    "preliminary_BOM_totals_USD": bom_totals,
}
(OUT / "calculation-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
