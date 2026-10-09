import {supabase} from '../lib/supabase'; import type {Filters,Project,ProgressUpdate,DashboardSummary} from '../types';
const base=import.meta.env.VITE_API_URL||'http://localhost:8000';
async function request<T>(path:string,init:RequestInit={}){const {data}=supabase?await supabase.auth.getSession():{data:{session:null}}; const headers=new Headers(init.headers); if(data.session)headers.set('Authorization',`Bearer ${data.session.access_token}`); if(!(init.body instanceof FormData))headers.set('Content-Type','application/json'); const r=await fetch(`${base}${path}`,{...init,headers}); if(!r.ok){let msg='Request failed';try{const e=await r.json();msg=e.detail||msg}catch{} throw new Error(msg)} return r.json() as Promise<T>}
function qs(filters:Filters){const p=new URLSearchParams(); Object.entries(filters).forEach(([k,v])=>v&&p.set(k,v)); return p.toString()?`?${p}`:''}
export const api={
 projects:(f:Filters={},opts:any={})=>request<{items:Project[];total:number;page:number;page_size:number}>(`/projects${qs({...f,...opts})}`),
 project:(id:string)=>request<Project>(`/projects/${id}`),
 progress:(id:string)=>request<ProgressUpdate[]>(`/projects/${id}/progress`),
 dashboard:(f:Filters={})=>request<DashboardSummary>(`/dashboard/summary${qs(f)}`),
 byYear:(f:Filters={})=>request<any[]>(`/dashboard/projects-by-year${qs(f)}`),
 byStatus:(f:Filters={})=>request<any[]>(`/dashboard/projects-by-status${qs(f)}`),
 bySector:(f:Filters={})=>request<any[]>(`/dashboard/projects-by-sector${qs(f)}`),
 recent:(f:Filters={})=>request<ProgressUpdate[]>(`/dashboard/recent-updates${qs(f)}`),
 create:(body:any)=>request<Project>('/projects',{method:'POST',body:JSON.stringify(body)}),
 update:(id:string,body:any)=>request<Project>(`/projects/${id}`,{method:'PUT',body:JSON.stringify(body)}),
 delete:(id:string)=>request<void>(`/projects/${id}`,{method:'DELETE'}),
 addProgress:(id:string,form:FormData)=>request<ProgressUpdate>(`/projects/${id}/progress`,{method:'POST',body:form}),
 deleteMedia:(mediaId:string)=>request<void>(`/progress-media/${mediaId}`,{method:'DELETE'})
};
