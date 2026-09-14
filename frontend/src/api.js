const B="/api";
async function r(p,o={}){const res=await fetch(B+p,o);if(!res.ok){const e=await res.json().catch(()=>({detail:res.statusText}));throw new Error(e.detail||"Failed")}return res.json()}
export const uploadCSV=f=>{const d=new FormData();d.append("file",f);return r("/datasets/upload",{method:"POST",body:d})};
export const listDatasets=()=>r("/datasets");
export const getDataset=id=>r(`/datasets/${id}`);
export const getItems=(id,p=1)=>r(`/datasets/${id}/items?page=${p}&page_size=20`);
export const createAnnotation=(id,b)=>r(`/items/${id}/annotations`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});
export const getAnnotations=id=>r(`/items/${id}/annotations`);
