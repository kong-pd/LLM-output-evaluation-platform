import{useState,useEffect}from"react";import{useParams}from"react-router-dom";import{getDataset,getItems,createAnnotation,getAnnotations,getAgreement,getDifficulty,getRCA,exportReport}from"../api";

function Badge({s}){if(s==null)return<span className="muted">—</span>;const v=Math.round(s*10)/10;const c=v>=4?"badge-green":v>=3?"badge-amber":"badge-red";return<span className={`badge ${c}`}>{v}</span>}
function Pct({v}){if(v==null)return"—";return Math.round(v*100)+"%"}
function Kappa({v}){if(v==null)return<span className="muted">—</span>;const c=v>=0.6?"badge-green":v>=0.4?"badge-amber":"badge-red";const l=v>=0.8?"almost perfect":v>=0.6?"substantial":v>=0.4?"moderate":v>=0.2?"fair":"slight";return<span className={`badge ${c}`}>{v} ({l})</span>}
function Diff({d}){const c=d==="hard"?"badge-red":d==="medium"?"badge-amber":"badge-green";return<span className={`badge ${c}`}>{d}</span>}
function ErrBadge({t}){if(!t)return null;const c={hallucination:"badge-red",contradicts:"badge-red",incomplete:"badge-amber",off_topic:"badge-amber",poor_reasoning:"badge-amber",no_error:"badge-green"}[t]||"badge-amber";return<span className={`badge ${c}`}>{t}</span>}

function AgreementPanel({id}){
const[data,setData]=useState(null);
useEffect(()=>{const load=()=>getAgreement(id).then(setData).catch(()=>{});load();const iv=setInterval(load,3000);return()=>clearInterval(iv)},[id]);
if(!data||!data.total_annotations)return null;
const dims=Object.entries(data.per_dimension||{});
const cm=data.confusion_matrix||[];
return(<div style={{border:"1px solid #e5e5e5",padding:16,borderRadius:6,marginTop:16}}>
<h2 style={{marginBottom:8}}>Agreement analysis</h2>
<p className="muted">{data.total_annotations} annotations · {data.agree_count} agree · {data.override_count} override</p>
<p style={{marginTop:8}}>Exact match: <b><Pct v={data.exact_match_rate}/></b> · Within ±1: <b><Pct v={data.close_match_rate}/></b> · Cohen's κ: <Kappa v={data.cohens_kappa}/></p>
{dims.length>0&&<table style={{marginTop:12}}><thead><tr><th>Dimension</th><th>Count</th><th>Exact</th><th>±1</th><th>κ</th><th>Auto</th><th>Human</th></tr></thead>
<tbody>{dims.map(([d,v])=><tr key={d}><td style={{fontWeight:500}}>{d}</td><td>{v.count}</td><td><Pct v={v.exact_match_rate}/></td><td><Pct v={v.close_match_rate}/></td><td><Kappa v={v.cohens_kappa}/></td><td>{v.avg_auto}</td><td>{v.avg_human}</td></tr>)}</tbody></table>}
{cm.length>0&&<div style={{marginTop:16}}><h3 style={{fontSize:14,marginBottom:8}}>Confusion matrix (auto ↓ vs human →)</h3>
<table><thead><tr><th>Auto\Human</th>{[1,2,3,4,5].map(h=><th key={h} style={{textAlign:"center"}}>{h}</th>)}</tr></thead>
<tbody>{cm.map(row=><tr key={row.auto_score}><td style={{fontWeight:500}}>{row.auto_score}</td>{[1,2,3,4,5].map(h=>{const v=row[`human_${h}`];return<td key={h} style={{textAlign:"center",background:v>0?(row.auto_score===h?"#dcfce7":"#fef3c7"):"transparent",fontWeight:v>0?600:400}}>{v||"·"}</td>})}</tr>)}</tbody></table></div>}
</div>)}

function RCAPanel({id}){
const[data,setData]=useState(null);
useEffect(()=>{getRCA(id).then(setData).catch(()=>{})},[id]);
if(!data||!data.total_items)return null;
return(<div style={{border:"1px solid #e5e5e5",padding:16,borderRadius:6,marginTop:16}}>
<h2 style={{marginBottom:8}}>Root cause analysis</h2>
<p className="muted">{data.total_items} items · {data.items_with_errors} with errors ({<Pct v={data.error_rate}/>})</p>
{data.avg_scores&&<div style={{marginTop:8}}><b>Average scores: </b>
{Object.entries(data.avg_scores).filter(([,v])=>v!==null).map(([k,v])=><span key={k} style={{marginRight:12}}>{k}: <Badge s={v}/></span>)}</div>}
{data.error_breakdown&&data.error_breakdown.length>0&&<div style={{marginTop:12}}><b>Error types:</b>
<table style={{marginTop:8}}><thead><tr><th>Type</th><th>Count</th><th>% of total</th></tr></thead>
<tbody>{data.error_breakdown.map(e=><tr key={e.type}><td><ErrBadge t={e.type}/></td><td>{e.count}</td><td><Pct v={e.pct}/></td></tr>)}</tbody></table></div>}
{data.pipeline_diagnosis&&data.pipeline_diagnosis.length>0&&<div style={{marginTop:12}}><b>Pipeline diagnosis:</b>
{data.pipeline_diagnosis.map((d,i)=><div key={i} style={{padding:8,margin:"6px 0",background:"#fef3c7",borderRadius:4,fontSize:13}}>
<b>{d.component}</b>: {d.issue} (avg: {d.avg_score}) → <i>{d.action}</i></div>)}</div>}
</div>)}

function DifficultyPanel({id}){
const[data,setData]=useState(null);
useEffect(()=>{getDifficulty(id).then(setData).catch(()=>{})},[id]);
if(!data||!data.items||!data.items.length)return null;
const hard=data.items.filter(i=>i.difficulty!=="easy");
if(!hard.length)return null;
return(<div style={{border:"1px solid #e5e5e5",padding:16,borderRadius:6,marginTop:16}}>
<h2 style={{marginBottom:8}}>Difficult items</h2>
<table style={{marginTop:8}}><thead><tr><th>#</th><th>Question</th><th>Avg</th><th>Weakest</th><th>Difficulty</th><th>Error</th></tr></thead>
<tbody>{hard.map(i=><tr key={i.row}><td>{i.row}</td><td style={{maxWidth:250,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{i.question}</td><td><Badge s={i.avg_score}/></td><td className="muted">{i.weakest_dimension}</td><td><Diff d={i.difficulty}/></td><td><ErrBadge t={i.error_type}/></td></tr>)}</tbody></table>
</div>)}

function Review({item,onDone}){
const allDims=["faithfulness","relevance","coherence","context_relevance","groundedness"];
const auto={faithfulness:item.auto_faithfulness,relevance:item.auto_relevance,coherence:item.auto_coherence,context_relevance:item.auto_context_relevance,groundedness:item.auto_groundedness};
const dims=allDims.filter(d=>auto[d]!=null);
const[scores,setScores]=useState({...auto});const[done,setDone]=useState([]);const[saving,setSaving]=useState(false);
useEffect(()=>{getAnnotations(item.id).then(a=>setDone(a.map(x=>x.dimension))).catch(()=>{})},[item.id]);
async function submit(d){setSaving(true);try{await createAnnotation(item.id,{dimension:d,human_score:scores[d],action:scores[d]===auto[d]?"agree":"override"});setDone([...done,d])}finally{setSaving(false)}}
return(<div style={{border:"1px solid #e5e5e5",padding:16,borderRadius:6,marginTop:16}}>
<h2>{item.question}</h2><p className="muted" style={{margin:"8px 0"}}><b>Context:</b> {item.context||"(none)"}</p><p style={{margin:"8px 0"}}><b>Answer:</b> {item.llm_answer}</p>
<p className="muted">Model: {item.auto_eval_model||"—"}{item.auto_error_type&&<> · Error: <ErrBadge t={item.auto_error_type}/></>}</p>
{dims.map(d=><div className="dim-row" key={d}><span style={{width:130,fontWeight:500}}>{d}</span><span className="muted">auto: <Badge s={auto[d]}/></span>
<select value={scores[d]??""} onChange={e=>setScores({...scores,[d]:parseFloat(e.target.value)})} disabled={done.includes(d)}>{[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}</select>
{done.includes(d)?<span className="badge badge-green">done</span>:<button onClick={()=>submit(d)} disabled={saving}>Submit</button>}</div>)}
<button style={{marginTop:12}} onClick={onDone}>Close</button></div>)}

export default function DatasetPage(){const{id}=useParams();const[ds,setDs]=useState(null);const[items,setItems]=useState([]);const[total,setTotal]=useState(0);const[page,setPage]=useState(1);const[rev,setRev]=useState(null);
useEffect(()=>{getDataset(id).then(setDs)},[id]);
useEffect(()=>{const load=()=>getItems(id,page).then(d=>{setItems(d.items);setTotal(d.total)}).catch(()=>{});load();const iv=setInterval(load,3000);return()=>clearInterval(iv)},[id,page]);
if(!ds)return<p className="muted">Loading...</p>;const pages=Math.ceil(total/20);
return(<div><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
<h1>{ds.name}</h1><button onClick={()=>exportReport(id)}>Export CSV</button></div>
<p className="muted">{ds.status} · {ds.evaluated_items}/{ds.total_items} evaluated · {ds.annotated_items}/{ds.total_items} annotated</p>
<AgreementPanel id={id}/><RCAPanel id={id}/><DifficultyPanel id={id}/>
{rev&&<Review item={rev} onDone={()=>{setRev(null);getItems(id,page).then(d=>{setItems(d.items);setTotal(d.total)})}}/>}
<table><thead><tr><th>#</th><th>Question</th><th>Faith.</th><th>Relev.</th><th>Coher.</th><th>Ctx.R</th><th>Grnd.</th><th>Error</th><th>Status</th><th></th></tr></thead>
<tbody>{items.map(i=><tr key={i.id}><td>{i.row_index+1}</td><td style={{maxWidth:200,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{i.question}</td><td><Badge s={i.auto_faithfulness}/></td><td><Badge s={i.auto_relevance}/></td><td><Badge s={i.auto_coherence}/></td><td><Badge s={i.auto_context_relevance}/></td><td><Badge s={i.auto_groundedness}/></td><td><ErrBadge t={i.auto_error_type}/></td><td className="muted">{i.auto_eval_status}</td><td>{i.auto_eval_status==="done"&&<button onClick={()=>setRev(i)}>Review</button>}</td></tr>)}</tbody></table>
{pages>1&&<div style={{marginTop:12,display:"flex",gap:8}}><button disabled={page<=1} onClick={()=>setPage(page-1)}>Prev</button><span className="muted">{page}/{pages}</span><button disabled={page>=pages} onClick={()=>setPage(page+1)}>Next</button></div>}</div>)}
