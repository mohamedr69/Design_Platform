exec((__import__('pathlib').Path(__file__).parent/'probe_correction.py').read_text().split('bad=scratch/')[0])
p=scratch/'stat-only.pdf';p.write_bytes(b'stat only; explicit reading supplied')
coverage={'outcome':'bounded','pages_total':13,'pages_visited':list(range(1,13)),'pages_skipped':[{'page':13,'reason':'page scan limit'}],'pages_failed':[],'promoted':False}
r=row({'records':[{'reference':'OLD-PARSER-APPROVAL','page':13,'status':'approved','revision':'R0','flags':[]}],'read_sha256':'new-bytes','profile':'default','parser_version':'older-defective-parser','read_at':'original-time'})
before=dp.parser_current(r)
ds.process(None,None,r,p,scratch,user_id=None,ocr=False,read=([],()),coverage=coverage)
data={'parser_current_before':before,'parser_current_after':dp.parser_current(r),'current_parser':dc.PARSER_VERSION,'envelope_parser':r.extracted['parser_version'],'mirror_status':r.status,'record':r.extracted['records'][0],'retained_summary':r.extracted.get('retained'),'reuse_sha':dp._previous_sha(r)}
(OUT/'retained_parser_probe.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
