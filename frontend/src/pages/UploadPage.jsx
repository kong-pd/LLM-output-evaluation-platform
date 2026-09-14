import{useState,useRef}from"react";import{useNavigate}from"react-router-dom";import{uploadCSV}from"../api";
export default function UploadPage(){const[u,setU]=useState(false);const[e,setE]=useState("");const f=useRef();const nav=useNavigate();
async function go(){const file=f.current.files[0];if(!file)return;setU(true);setE("");try{const ds=await uploadCSV(file);nav(`/datasets/${ds.id}`)}catch(err){setE(err.message)}finally{setU(false)}}
return(<div><h1>Upload Dataset</h1><p className="muted">CSV with columns: question, context (optional), llm_answer</p><br/><input ref={f} type="file" accept=".csv"/><button className="primary" onClick={go} disabled={u}>{u?"Uploading...":"Upload"}</button>{e&&<p style={{color:"red",marginTop:8}}>{e}</p>}</div>)}
