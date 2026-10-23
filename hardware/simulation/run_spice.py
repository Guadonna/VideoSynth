#!/usr/bin/env python3
"""Use system libngspice via its supported shared-library interface (no root needed)."""
import ctypes,ctypes.util,json,math,pathlib,os
root=pathlib.Path(__file__).resolve().parents[2];os.chdir(root)
lib=ctypes.CDLL(ctypes.util.find_library('ngspice') or 'libngspice.so.0')
LOG=[]
CB=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_void_p)
@CB
def output(s,ident,user):LOG.append(s.decode(errors='replace'));return 0
lib.ngSpice_Init.argtypes=[CB,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
lib.ngSpice_Init(output,None,None,None,None,None,None)
lib.ngSpice_Command.argtypes=[ctypes.c_char_p]
code=lib.ngSpice_Command(b'source hardware/simulation/cv-linear.cir')
(root/'hardware/verification/ngspice.log').write_text('\n'.join(LOG)+'\n')
if code or any('Error' in x for x in LOG):raise RuntimeError('\n'.join(LOG))
def data(name):return [[float(s) for s in row.split()] for row in (root/'hardware/verification'/name).read_text().splitlines()[1:] if row.strip()]
dc=data('cv-dc.txt');ac=data('cv-ac.txt');at100=min(ac,key=lambda r:abs(r[0]-100));gain0=.12*100000/104700
expected=[(1.65-.12*x)*100000/104700 for x,*_ in dc]
err=max(abs(row[1]-e) for row,e in zip(dc,expected));assert err<5e-6,(err,dc[:1])
mag=math.hypot(*at100[1:3]);atten=-20*math.log10(mag/gain0);assert .8<atten<1.1,atten
summary={'solver':'ngspice shared library','model_scope':'ideal opamp, linear powered-on CV gain/filter only','dc_points':len(dc),'ac_points':len(ac),'max_dc_error_V':err,'attenuation_at_100_Hz_dB':atten,'adc_at_minus10_V':dc[0][1],'adc_at_plus10_V':dc[-1][1],'not_simulated':['power-off CV protection','semiconductor overload and ESD','buck switching/transients','video amplifier parasitics','MCU/DMA']}
(root/'hardware/verification/spice-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
