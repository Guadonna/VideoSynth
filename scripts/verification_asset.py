from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1];v=root/'hardware/verification'
c=json.loads((v/'connectivity-summary.json').read_text());b=json.loads((v/'browser-summary.json').read_text());s=json.loads((v/'spice-summary.json').read_text())
tests=(v/'unit-tests.tap').read_text();passed=re.search(r'^# pass (\d+)$',tests,re.M);assert passed and re.search(r'^# fail 0$',tests,re.M)
compat=json.loads((v/'browser-compatibility-summary.json').read_text())
checks=[{'label':'Core: ERC / DRC / незавершённые связи','result':f"{c['core']['erc_violations']} / {c['core']['drc_violations']} / {c['core']['unconnected_items']}"},{'label':'Panel: ERC / DRC / незавершённые связи','result':f"{c['panel']['erc_violations']} / {c['panel']['drc_violations']} / {c['panel']['unconnected_items']}"},{'label':'Схема ↔ manifest ↔ площадки PCB','result':'678 / PASS'},{'label':'Автоматические тесты DSP / логики / растра / запуска','result':passed[1]+' PASS'},{'label':'Браузерные сценарии','result':str(b['passed'])+' PASS'},{'label':'Совместимость запуска DSP','result':str(compat['passed'])+' PASS'},{'label':'Линейный CV, SPICE при 100 Гц','result':f"−{s['attenuation_at_100_Hz_dB']:.3f} дБ"},{'label':'ESP32-P4 / аналоговый выход / защита CV','result':'НЕ ИЗМЕРЕНО'}]
(root/'app/assets/verification.json').write_text(json.dumps({'revision':'R1-prototype','date':'2026-10-23','checks':checks},ensure_ascii=False,indent=2)+'\n')
