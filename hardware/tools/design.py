"""Single-source electrical connectivity and placement for VideoSynth R1.
Pin numbers are physical package pins, NOT invented logical bus indices.
Run with /usr/bin/python3 (KiCad pcbnew). No production order is created.
"""
from pathlib import Path
import json, math, csv, uuid, os
ROOT=Path(__file__).resolve().parents[2]
PARTS=[]
CNT={}
BOARD='core'; GROUP='Power'
RFP='Resistor_SMD:R_0805_2012Metric'
CFP='Capacitor_SMD:C_0805_2012Metric'
SO=lambda n,w,l,p: f'Package_SO:SOIC-{n}_{w}x{l}mm_P{p}mm'
SOT='Package_TO_SOT_SMD:SOT-23'
HDR=lambda n:f'Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical'
IDC='Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical'
def add(prefix,value,fp,pins,xy,mpn='',angle=0,side='F',names=None,types=None,note=''):
 key=(BOARD,prefix);CNT[key]=CNT.get(key,0)+1;ref=prefix+str(CNT[key])
 p=dict(board=BOARD,group=GROUP,ref=ref,value=value,footprint=fp,pins={str(k):v for k,v in pins.items()},xy=list(xy),angle=angle,side=side,mpn=mpn or (value if prefix in ['U','D'] else ''),note=note,names={str(k):v for k,v in (names or {}).items()},types={str(k):v for k,v in (types or {}).items()})
 PARTS.append(p);return p

def R(v,a,b,xy,**kw):return add('R',v,RFP,{1:a,2:b},xy,**kw)
def C(v,a,b,xy,**kw):return add('C',v,CFP,{1:a,2:b},xy,**kw)
def dec(net,xy):return C('100n 16V X7R',net,'GND',xy)
def flag(net):return add('#FLG',net,'',{1:net},(0,0),types={1:'power_out'},note='ERC power source assertion; no physical part')
def chip(value,fp,pins,xy,names,types=None,**kw):return add('U',value,fp,pins,xy,names=names,types=types or {},**kw)
# CORE, 140 x 105 mm, 4 copper layers: F / GND / In2 signal / B.
# Eurorack standard: pins 1/2 -12, 3..8 GND, 9/10 +12. Negative rail intentionally unused.
add('J','EURORACK_10','Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical',{1:None,2:None,**{i:'GND' for i in range(3,9)},9:'EUR_12',10:'EUR_12'},(7,87),note='Stripe = pins 1/2, -12 V NC. Use keyed 10-pin ribbon.')
add('F','750mA HOLD 33V','Fuse:Fuse_1812_4532Metric',{1:'EUR_12',2:'FUSED_12'},(20,91),mpn='Bourns MF-MSMF075-2')
add('D','SS34','Diode_SMD:D_SMA',{1:'VIN',2:'FUSED_12'},(29,91),names={1:'K',2:'A'},note='Series reverse polarity diode, 40 V')
add('D','SMBJ15A','Diode_SMD:D_SMB',{1:'VIN',2:'GND'},(29,84),names={1:'K',2:'A'},note='TVS after fuse/series diode; surge qualification required')
add('C','22u 35V X7R','Capacitor_SMD:C_1210_3225Metric',{1:'VIN',2:'GND'},(37,94),mpn='GRM32ER7YA226KE15L');C('100n 50V X7R','VIN','GND',(49,85))
chip('TPS54302DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:'GND',2:'SW',3:'VIN',4:'FB',5:'EN_BUCK',6:'BOOT'},(46,88),{1:'GND',2:'SW',3:'VIN',4:'FB',5:'EN',6:'BOOT'},{1:'power_in',2:'power_out',3:'power_in',4:'input',5:'input',6:'passive'},angle=180)
C('100n 16V X7R','BOOT','SW',(43,91))
add('L','6.8uH verify Isat','Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm',{1:'SW',2:'V5'},(55,88),mpn='SRP7028A-6R8M')
C('22u 10V X7R','V5','GND',(64,87));C('22u 10V X7R','V5','GND',(64,92))
R('100k 1%','V5','FB',(53,96));R('13.3k 1%','FB','GND',(46,96));C('75p C0G','V5','FB',(59,96))
R('100k 1%','VIN','EN_BUCK',(37,80));R('24.9k 1%','EN_BUCK','GND',(44,77))
R('1k 1%','V5','GND',(72,92),note='Rail discharge / small fault-current sink; 25 mW nominal')
add('J','MODULE_5VP_GND',HDR(2),{1:'V5',2:'GND'},(36,72),note='Harness to Olimex POE_PWR1: our pin1 -> module pin4; our pin2 -> module pin3. Pins1/2 PoE never connected.')
for n in ['GND','VIN','V5','V3V3']:flag(n)
GROUP='Module and panel interface'
ext1={1:None,2:'GND',3:None,4:None,5:'SPI_SCK',6:'ADC_CS',7:'TFT_CS',8:'I2C_SDA',9:'I2C_SCL',**{10+i:f'VID_D{i}' for i in range(8)},18:'CLK_P4',19:'TFT_DC',20:'TFT_RST'}
ext1[1]='V3V3'
# V3V3 is exclusively the module output; do not connect a second regulator.
add('J','OLIMEX_EXT1','Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical',ext1,(13,67.5),angle=180,note='Olimex ESP32-P4-DevKit Rev.D1 EXT1, top-view exact pin correspondence')
ext2={1:None,2:'GND',3:'SPI_MISO',4:'SPI_MOSI',5:None,6:None,7:None,8:None,9:None,10:None,11:'DAC_SLEEP',12:'UI_IRQ2',13:'UI_IRQ1',14:None,15:'GND',16:None,17:None,18:'GND',19:None,20:None}
add('J','OLIMEX_EXT2','Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical',ext2,(38.4,67.5),angle=180,note='EXT2 pin1 +5V intentionally NC. Supply through POE_PWR1 only. REMOVE module FET2 to disconnect USB power.')
panelpins={1:'V3V3',2:'GND',3:'I2C_SDA',4:'I2C_SCL',5:'UI_IRQ1',6:'UI_IRQ2',7:'POT_MUX_A',8:'GND',9:'POT_MUX_B',10:'GND',11:'TFT_SCK',12:'TFT_MOSI',13:'TFT_CS',14:'TFT_DC',15:'TFT_RST',16:'GND',17:'CV1_RAW',18:'GND',19:'CV2_RAW',20:'GND'}
add('J','PANEL_20',IDC,panelpins,(128,14),note='Straight-through keyed cable <=50 mm, same pin numbers on panel.')
R('33','SPI_SCK','TFT_SCK',(119,8));R('33','SPI_MOSI','TFT_MOSI',(119,13))
R('2.2k','V3V3','I2C_SDA',(110,8));R('2.2k','V3V3','I2C_SCL',(110,13))
R('10k','V3V3','UI_IRQ1',(101,8));R('10k','V3V3','UI_IRQ2',(101,13))
R('10k','V3V3','ADC_CS',(92,8));R('10k','V3V3','TFT_CS',(92,13));R('100k','V3V3','DAC_SLEEP',(85,59))
C('10u 10V X7R','V3V3','GND',(118,22))
GROUP='Video DAC and clock'
add('Y','27.000MHz 3V3','Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',{1:'V3V3',2:'GND',3:'CLK27',4:'V3V3'},(54,59),mpn='ASE-27.000MHZ-LC-T',names={1:'OE',2:'GND',3:'OUT',4:'VDD'},types={1:'input',2:'power_in',3:'output',4:'power_in'})
dec('V3V3',(48,59));R('33','CLK27','CLK_P4',(48,53))
chip('SN74LVC1G04DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'CLK27',3:'GND',4:'CLK_INV',5:'V3V3'},(63,60),{1:'NC',2:'A',3:'GND',4:'Y',5:'VCC'},{2:'input',3:'power_in',4:'output',5:'power_in'})
dec('V3V3',(63,55));R('33','CLK_INV','DAC_CLK',(69,60))
# PARLIO must launch data on CLK27 rising edge, DAC latches on inverted edge.
vidpins={**{8-i:f'DAC_D{i}' for i in range(8)},**{i:None for i in list(range(9,15))+[25]},15:'DAC_SLEEP',16:'GND',17:'DAC_REF',18:'DAC_FSADJ',19:'DAC_COMP1',20:'GND',21:'DAC_B',22:'DAC_A',23:'DAC_COMP2',24:'V5A',26:'GND',27:'V3V3',28:'DAC_CLK'}
vidnames={**{8-i:f'DB{i}' for i in range(8)},15:'SLEEP',16:'REFLO',17:'REFIO',18:'FSADJ',19:'COMP1',20:'ACOM',21:'IOUTB',22:'IOUTA',23:'COMP2',24:'AVDD',26:'DCOM',27:'DVDD',28:'CLOCK'}
vidtypes={**{i:'input' for i in range(1,9)},15:'input',20:'power_in',21:'output',22:'output',24:'power_in',26:'power_in',27:'power_in',28:'input'}
chip('AD9708ARUZ','Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm',vidpins,(81,72),vidnames,vidtypes)
for i in range(8):R('33',f'VID_D{i}',f'DAC_D{i}',(47+(i%2)*7,20+(i//2)*6))
# First-order passive rail filtering; 1 ohm drop measured at bringup.
R('1 1%','V5','V5A',(74,85));C('22u 10V X7R','V5A','GND',(82,86));dec('V5A',(91,75));dec('V3V3',(71,71))
C('100n 16V X7R','DAC_REF','GND',(78,81));R('1.91k 0.1%','DAC_FSADJ','GND',(88,82))
C('100n 16V X7R','DAC_COMP1','V5A',(94,81));C('100n 16V X7R','DAC_COMP2','GND',(96,69))
R('49.9 0.1%','DAC_B','GND',(92,63));R('49.9 0.1%','DAC_A','GND',(103,70))
chip('THS7314D',SO(8,'3.9','4.9','1.27'),{1:'DAC_A',2:'GND',3:'GND',4:'V5A',5:'GND',6:None,7:None,8:'VIDEO_DRV'},(115,73),{1:'IN1',2:'IN2',3:'IN3',4:'VS',5:'GND',6:'OUT3',7:'OUT2',8:'OUT1'},{1:'input',2:'input',3:'input',4:'power_in',5:'power_in',6:'output',7:'output',8:'output'},note='Gain 2, 8.5MHz fifth-order LPF, +285mV output level shift')
dec('V5A',(115,67));C('10u 10V X7R','V5A','GND',(115,81))
R('75 1%','VIDEO_DRV','CVBS',(125,73))
add('J','CVBS_COAX',HDR(2),{1:'CVBS',2:'GND'},(134,73),note='Short 75 ohm coax to panel RCA; no second 75 ohm shunt on PCB.')
for n,xy in [('DAC_A',(103,65)),('CVBS',(132,82)),('CLK_P4',(46,47))]:add('TP',n,'TestPoint:TestPoint_Pad_D1.5mm',{1:n},xy)
flag('V5A')
GROUP='CV protection and control ADC'
# Four op-amps: two inverting CV scalers and two pot mux buffers, on 5 V.
# CV transfer = 1.65 - 0.12 Vin, using 12.4k/10k bias divider and 100k/12k gain.
R('12.4k 0.1%','V3V3','CV_BIAS',(65,8));R('10k 0.1%','CV_BIAS','GND',(73,8));C('1u 10V X7R','CV_BIAS','GND',(81,8))
for ch,x in [(1,68),(2,98)]:
 R('100k 0.1%',f'CV{ch}_RAW',f'CV{ch}_INV',(x-10,20))
 R('12k 0.1%',f'CV{ch}_INV',f'CV{ch}_AMP',(x,31))
 C('47n 5% X7R',f'CV{ch}_INV',f'CV{ch}_AMP',(x,36))
 R('4.7k 1%',f'CV{ch}_AMP',f'CV{ch}_FILTER',(x+8,31))
 C('100n 5% X7R',f'CV{ch}_FILTER','GND',(x+8,36))
 # External two Schottky diodes: lower clamp to ground, upper clamp to V3V3.
 add('D','BAT54S',SOT,{1:'GND',2:'V3V3',3:f'CV{ch}_FILTER'},(x+8,42),names={1:'A1',2:'K2',3:'K1_A2'},note='Series pair clamp. Exact forward voltage and power-off behavior require bench test.')
 # ADC input has powered-off isolation after the current-limited/clamped node.
 chip('OPA2197IDR',SO(8,'3.9','4.9','1.27'),{1:f'CV{ch}_AMP',2:f'CV{ch}_INV',3:'CV_BIAS',4:'GND',5:'POT_MUX_'+('A' if ch==1 else 'B'),6:f'POTBUF_{ch}',7:f'POTBUF_{ch}',8:'V5'},(x,24),{1:'OUT_A',2:'IN_A-',3:'IN_A+',4:'V-',5:'IN_B+',6:'IN_B-',7:'OUT_B',8:'V+'},{1:'output',2:'input',3:'input',4:'power_in',5:'input',6:'input',7:'output',8:'power_in'})
 dec('V5',(x-4,15));R('47',f'POTBUF_{ch}',f'POT_ADC{ch}',(x-10,42));C('1n C0G',f'POT_ADC{ch}','GND',(x-10,47))
R('1k 1%','V3V3','GND',(111,38),note='3.3 mA bleeder absorbs specified clamp-current budget; not a replacement for power-off test')
chip('TMUX1511PWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',{1:'V3V3',2:'CV1_FILTER',3:'CV1_ADC',4:'V3V3',5:'CV2_FILTER',6:'CV2_ADC',7:'GND',8:None,9:'GND',10:'GND',11:None,12:'GND',13:'GND',14:'V3V3'},(119,36),{1:'SEL1',2:'S1',3:'D1',4:'SEL2',5:'S2',6:'D2',7:'GND',8:'D3',9:'S3',10:'SEL3',11:'D4',12:'S4',13:'SEL4',14:'VDD'},{1:'input',4:'input',7:'power_in',10:'input',13:'input',14:'power_in'},note='Powered-off isolation valid only for signal nodes 0..3.6V; verify both CV fault polarities.')
dec('V3V3',(117,43));R('100k','CV1_ADC','GND',(124,47));R('100k','CV2_ADC','GND',(132,47))
# Switch output bias resistors load the 4.7k LPF; calibrate gain (100k/(100k+4.7k)).
chip('MCP3204-CI/SL',SO(14,'3.9','8.7','1.27'),{1:'POT_ADC1',2:'POT_ADC2',3:'CV1_ADC',4:'CV2_ADC',5:None,6:None,7:'GND',8:'ADC_CS',9:'SPI_MOSI',10:'SPI_MISO',11:'SPI_SCK',12:'GND',13:'V3V3',14:'V3V3'},(104,52),{1:'CH0',2:'CH1',3:'CH2',4:'CH3',5:'NC',6:'NC',7:'DGND',8:'CS',9:'DIN',10:'DOUT',11:'CLK',12:'AGND',13:'VREF',14:'VDD'},{1:'input',2:'input',3:'input',4:'input',7:'power_in',8:'input',9:'input',10:'tri_state',11:'input',12:'power_in',13:'power_in',14:'power_in'})
dec('V3V3',(96,52));C('1u 10V X7R','V3V3','GND',(96,57))
for n,xy in [('V5',(72,96)),('V3V3',(118,94)),('GND',(126,94)),('CV1_ADC',(120,53)),('CV2_ADC',(129,53))]:add('TP',n,'TestPoint:TestPoint_Pad_D1.5mm',{1:n},xy)
# PANEL, 208.28 x 108 mm, controls/LEDs on front, other SMD on back.
BOARD='panel'; GROUP='Panel interface and I2C controls'
add('J','CORE_20',IDC,panelpins,(194,8),side='B',note='Pin-for-pin cable to core PANEL_20, inspect pin1 on both faces')
for n in ['V3V3','GND']:flag(n)
C('10u 10V X7R','V3V3','GND',(185,8),side='B')
# Expanders have no buttons on the matrix; they scan actual UI controls and select mux channels.
for ui,xy in [(1,(156,24)),(2,(181,24))]:
 pins={**{i:None for i in range(1,29)},9:'V3V3',10:'GND',12:'I2C_SCL',13:'I2C_SDA',15:'GND' if ui==1 else 'V3V3',16:'GND',17:'GND',18:'UI_RESET',20:f'UI_IRQ{ui}'}
 names={9:'VDD',10:'VSS',11:'NC',12:'SCL',13:'SDA',14:'NC',15:'A0',16:'A1',17:'A2',18:'RESET',19:'INTB',20:'INTA'}
 for i in range(8):names[i+1]=f'GPB{i}';names[i+21]=f'GPA{i}'
 if ui==1:
  for i in range(8):pins[21+i]=f'BUTTON{i}'
  for i in range(6):pins[1+i]=f'LED{i}'
  pins[7]='BL_GATE'
 else:
  for i in range(4):pins[21+i]=f'MUX_S{i}'
  for i,n in enumerate(['ENC_X_A','ENC_X_B','ENC_Y_A','ENC_Y_B']):pins[25+i]=n
 typ={9:'power_in',10:'power_in',12:'input',13:'bidirectional',15:'input',16:'input',17:'input',18:'input',19:'open_collector',20:'open_collector',**{i:'bidirectional' for i in list(range(1,9))+list(range(21,29))}}
 chip('MCP23017-E/SO','Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm',pins,xy,names,typ,side='B',note='I2C address '+('0x20' if ui==1 else '0x21')+'; IRQ open-drain active-low; configure output latches before direction.')
 decp=dec('V3V3',(xy[0]-10,xy[1]));decp['side']='B'
R('10k','V3V3','UI_RESET',(187,88),side='B');C('100n 16V X7R','UI_RESET','GND',(187,94),side='B')
# Pot mux address defaults to zero until MCP23017 initialized.
for i in range(4):R('100k',f'MUX_S{i}','GND',(137,20+i*6),side='B')
GROUP='Potentiometers and multiplexers'
# The RK09K shaft is at footprint origin +(7,2.5) mm.
for osc in range(6):
 for param in range(4):
  k=osc*4+param;x=12+22*osc;y=16+20*param
  add('RV','10k B linear','Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Vertical',{1:'GND',2:f'POT{k:02}',3:'V3V3','MP':'GND'},(x-7,y-2.5),mpn='ALPS RK09K1130A6S',note=f'{["H1","H2","H3","V1","V2","V3"][osc]} {["frequency","fine","phase","morph"][param]}; shaft=({x},{y}) mm')
for mux,xy in [(0,(45,46)),(1,(111,46))]:
 # CD74HC4067M channels are not sequential package pins.
 chpins=[9,8,7,6,5,4,3,2,23,22,21,20,19,18,17,16]
 pins={1:'POT_MUX_'+('A' if mux==0 else 'B'),10:'MUX_S0',11:'MUX_S1',12:'GND',13:'MUX_S3',14:'MUX_S2',15:'GND',24:'V3V3'}
 for ch,pin in enumerate(chpins):pins[pin]=f'POT{mux*12+ch:02}' if ch<12 else 'GND'
 names={1:'COM',10:'S0',11:'S1',12:'GND',13:'S3',14:'S2',15:'EN_N',24:'VCC',**{p:f'CH{i}' for i,p in enumerate(chpins)}}
 chip('CD74HC4067M96','Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm',pins,xy,names,{10:'input',11:'input',12:'power_in',13:'input',14:'input',15:'input',24:'power_in'},side='B',angle=90)
 c=dec('V3V3',(xy[0]+10,xy[1]));c['side']='B'
# LED and buttons located at 94mm (front). THT and bottom SMD do not share keepout.
GROUP='Buttons encoders and display'
for i in range(8):
 x=12+i*22 if i<6 else 156+(i-6)*28;y=94 if i<6 else 82
 add('SW',('OSC'+str(i+1) if i<6 else ['MODE','SLOT'][i-6]),'Button_Switch_THT:SW_PUSH_6mm',{1:f'BUTTON{i}',2:'GND'},(x-3.25,y-2.25),mpn='Omron B3F-1000',note='Momentary; latched in software')
 R('10k','V3V3',f'BUTTON{i}',(x,100 if i<6 else 90),side='B')
 if i<6:
  add('D','LED green','LED_SMD:LED_0603_1608Metric',{1:f'LED{i}',2:f'LED_A{i}'},(x+7,94),mpn='LTST-C190KGKT',names={1:'K',2:'A'})
  R('1k','V3V3',f'LED_A{i}',(x+7,100),side='B')
for i,x in enumerate([155,183]):
 axis='X' if i==0 else 'Y'
 add('ENC','EC11E1534408','Rotary_Encoder:RotaryEncoder_Alps_EC11E_Vertical_H20mm',{ 'A':f'ENC_{axis}_A','B':f'ENC_{axis}_B','C':'GND','MP':'GND'},(x,62),mpn='ALPS EC11E1534408')
 for k in range(2):
  net=f'ENC_{axis}_'+('A' if k==0 else 'B');R('10k','V3V3',net,(x-4+k*8,69),side='B');C('10n 16V X7R',net,'GND',(x-4+k*8,74),side='B')
add('J','TFT_SPI_3V3',HDR(8),{1:'V3V3',2:'GND',3:'TFT_MOSI',4:'TFT_SCK',5:'TFT_CS',6:'TFT_DC',7:'TFT_RST',8:'TFT_BL'},(143,12),note='Harness: Waveshare 2.4inch LCD Module: VCC GND DIN CLK CS DC RST BL. Confirm ordered revision before assembly.')
# TFT BL is a logic input, NOT a naked LED supply; no current driven from expander.
chip('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'GND',2:'BL_GATE',3:'GND',4:'TFT_BL',5:'V3V3'},(154,40),{1:'OE_N',2:'A',3:'GND',4:'Y',5:'VCC'},{1:'input',2:'input',3:'power_in',4:'output',5:'power_in'},side='B')
R('100k','BL_GATE','GND',(164,40),side='B');c=dec('V3V3',(154,46));c['side']='B'
for ch,x in [(1,153),(2,177)]:
 add('J','CV'+str(ch),'Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles',{'T':f'CV{ch}_RAW','TN':'GND','S':'GND'},(x,90),mpn='WQP-PJ398SM',note='Verify physical sleeve/tip orientation. Normalling contact tied to GND makes unplugged CV 0 V.')
# Panel-mounted RCA is connected directly by coax from core (no extra panel trace).
# Mounting holes are mechanical and excluded from electrical BOM.
BOARD_CONFIG={'core':{'size':[140,105],'holes':[(4,4),(136,4),(24,101),(136,101)],'layers':4},'panel':{'size':[208.28,108],'holes':[(3,3),(205.28,3),(3,105),(205.28,105)],'layers':4}}

def dump():
 (ROOT/'hardware/design.json').write_text(json.dumps({'revision':'R1-prototype','boards':BOARD_CONFIG,'parts':PARTS},indent=2)+'\n')
 with (ROOT/'hardware/bom-r1.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['board','reference','value','manufacturer_part','footprint','assembly','qualification','note'])
  for p in PARTS:
   if p['footprint']:w.writerow([p['board'],p['ref'],p['value'],p['mpn'],p['footprint'],'SMD' if ('SMD' in p['footprint'] or p['ref'].startswith('U') or p['ref'].startswith('Y') or p['footprint'].startswith('Fuse:')) else 'THT/module','candidate MPN: approve exact orderable part' if p['mpn'] else 'MPN to select: verify value / rating / package',p['note']])
if __name__=='__main__':dump();print(len(PARTS),'electrical symbols')
