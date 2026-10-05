from pathlib import Path
import ast,copy,importlib.util,json
R=Path(__file__).parent
S=Path('C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15/evidence/r15')
spec=importlib.util.spec_from_file_location('bc',S/'boq_contract.py');bc=importlib.util.module_from_spec(spec);spec.loader.exec_module(bc)
def e(id,y,description,part,qty):return dict(id=id,page=1,y=y,description=description,part_number=part,quantity=qty)
def t(n,description,part,qty,y=None):
 d=dict(ordinal=n,page=1,description=description,part_number=part,quantity=qty)
 if y is not None:d['y']=y
 return d
# Verified source middle row divides the rows above and below it.
truth=[t(1,'Manual call point','MCP',1),t(2,'Control panel','PANEL',1,200),t(3,'Manual call point with cover','MCP',2)]
emitted=[e('anchor',200,'Control panel','PANEL',1),e('below-anchor',300,'Manual call point','MCP',1)]
r=bc.join_rows(emitted,truth)
# The below-anchor row must not match truth row 1 above verified row 2.
wrong=[p for p in r['pairs'] if p[0]=='below-anchor' and p[1]==1 and p[2].startswith('matched')]
control=bc.join_rows([e('above-anchor',100,'Manual call point','MCP',1),emitted[0]],truth)
# Conflicting nearby positions must propagate as held in the replay as well.
amb_t=[t(6,'Speaker','PT-1S',1,100)]
amb_e=[e('a',95,'Speaker','PT-1S',1),e('b',105,'Speaker','PT-1S',1)]
amb=bc.join_rows(amb_e,amb_t)
tree=ast.parse((S/'replay_boq_r15.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='classify')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'replay_boq_r15.py','exec'),ns)
pair_of={ei:(ti,st) for ei,ti,st in amb['pairs']}
replayed={ei:ns['classify']({'accepted_by_reader':True,'state':'validated'},None,pair_of.get(ei,(None,None))[1],None,None) for ei in ('a','b')}
out={'mixed_geometry':{'truth':truth,'emitted':emitted,'join':r,'crossed_verified_anchor':bool(wrong),'false_correct_credit':bool(wrong) and bc.quantities_equal(1,truth[0]['quantity']) and not bc.quantities_equal(1,truth[2]['quantity']), 'above_anchor_control':control},'geometry_ambiguity':{'truth':amb_t,'emitted':amb_e,'join':amb,'replay_outcomes':replayed}}
(R/'ADDITIONAL-PROBES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
