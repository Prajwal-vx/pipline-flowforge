import { Activity, BarChart3, Box, GitBranch, LayoutDashboard, LogOut, Plug, Settings, Zap } from 'lucide-react';

export default function Sidebar({page,setPage}:{page:string;setPage:(p:string)=>void}){
 const items=[['dashboard',LayoutDashboard,'Dashboard'],['workflows',GitBranch,'Workflows'],['executions',Activity,'Executions'],['integrations',Plug,'Integrations'],['analytics',BarChart3,'Analytics']];
 return <aside className="sidebar">
   <div className="brand"><div className="brandmark"><Zap size={18}/></div><div><strong>FlowForge</strong><span>Automation OS</span></div></div>
   <div className="nav-label">WORKSPACE</div>
   {items.map(([id,Icon,label])=><button key={id as string} className={`nav-item ${page===id?'active':''}`} onClick={()=>setPage(id as string)}><Icon size={17}/><span>{label as string}</span></button>)}
   <div className="nav-spacer"/>
   <button className="nav-item"><Settings size={17}/><span>Settings</span></button>
   <button className="nav-item" onClick={()=>{localStorage.removeItem('flowforge_token');location.reload()}}><LogOut size={17}/><span>Sign out</span></button>
   <div className="sidebar-footer"><Box size={15}/><span>v1.0.0 · Local Engine</span></div>
 </aside>
}
