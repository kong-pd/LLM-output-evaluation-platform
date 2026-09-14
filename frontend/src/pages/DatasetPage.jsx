import{useState,useEffect}from"react";import{useParams}from"react-router-dom";import{getDataset,getItems,createAnnotation,getAnnotations}from"../api";
function Badge({s}){if(s==null)return<span className="muted">—</span>;const v=Math.round(s*10)/10;const c=v>=4?"badge-green":v>=3?"badge-amber":"badge-red";return<span className={`badge ${c}`}>{v}</span>}

function Review({item,onDone}){const dims=["faithfulness","relevance","coherence"];const auto={faithfulness:item.auto_faithfulness,relevance:item.auto_relevance,coherence:item.auto_coherence};
const[scores,setScores]=useState({...auto});const[done,setDone]=useState([]);const[saving,setSaving]=useState(false);
useEffect(()=>{getAnnotations(item.id).then(a=>setDone(a.map(x=>x.dimension))).catch(()=>{})},[item.id]);
async function submit(d){setSaving(true);try{await createAnnotation(item.id,{dimension:d,human_score:scores[d],action:scores[d]===auto[d]?"agree":"override"});setDone([...done,d])}finally{setSaving(false)}}
return(<div className="review-box"><h2>{item.question}</h2><p className="muted" style={{margin:"8px 0"}}><b>Context:</b> {item.context||"(none)"}</p><p style={{margin:"8px 0"}}><b>Answer:</b> {item.llm_answer}</p><p className="muted">Model: {item.auto_eval_model||"—"}</p>
{dims.map(d=><div className="dim-row" key={d}><span style={{width:100,fontWeight:500}}>{d}</span><span className="muted">auto: <Badge s={auto[d]}/></span>
<select value={scores[d]??""} onChange={e=>setScores({...scores,[d]:parseFloat(e.target.value)})} disabled={done.includes(d)}>{[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}</select>
{done.includes(d)?<span className="badge badge-green">done</span>:<button onClick={()=>submit(d)} disabled={saving}>Submit</button>}</div>)}
<button style={{marginTop:12}} onClick={onDone}>Close</button></div>)}

export default function DatasetPage(){const{id}=useParams();const[ds,setDs]=useState(null);const[items,setItems]=useState([]);const[total,setTotal]=useState(0);const[page,setPage]=useState(1);const[rev,setRev]=useState(null);
useEffect(()=>{getDataset(id).then(setDs)},[id]);
useEffect(()=>{const load=()=>getItems(id,page).then(d=>{setItems(d.items);setTotal(d.total)}).catch(()=>{});load();const iv=setInterval(load,3000);return()=>clearInterval(iv)},[id,page]);
if(!ds)return<p className="muted">Loading...</p>;const pages=Math.ceil(total/20);
return(<div><h1>{ds.name}</h1><p className="muted">{ds.status} · {ds.evaluated_items}/{ds.total_items} evaluated · {ds.annotated_items}/{ds.total_items} annotated</p>
{rev&&<Review item={rev} onDone={()=>{setRev(null);getItems(id,page).then(d=>{setItems(d.items);setTotal(d.total)})}}/>}
<table><thead><tr><th>#</th><th>Question</th><th>Faith.</th><th>Relev.</th><th>Coher.</th><th>Status</th><th></th></tr></thead>
<tbody>{items.map(i=><tr key={i.id}><td>{i.row_index+1}</td><td style={{maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{i.question}</td><td><Badge s={i.auto_faithfulness}/></td><td><Badge s={i.auto_relevance}/></td><td><Badge s={i.auto_coherence}/></td><td className="muted">{i.auto_eval_status}</td><td>{i.auto_eval_status==="done"&&<button onClick={()=>setRev(i)}>Review</button>}</td></tr>)}</tbody></table>
{pages>1&&<div style={{marginTop:12,display:"flex",gap:8}}><button disabled={page<=1} onClick={()=>setPage(page-1)}>Prev</button><span className="muted">{page}/{pages}</span><button disabled={page>=pages} onClick={()=>setPage(page+1)}>Next</button></div>}</div>)}
