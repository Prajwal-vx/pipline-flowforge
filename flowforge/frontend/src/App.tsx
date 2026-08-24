import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import WorkflowBuilder from './workflow/WorkflowBuilder';
import './styles.css';

export default function App(){const [page,setPage]=useState('dashboard');const [workflowId,setWorkflowId]=useState<string|undefined>();const [token]=useState(localStorage.getItem('flowforge_token')); if(!token)return <Login/>; if(page==='workflows'&&workflowId!==undefined)return <WorkflowBuilder id={workflowId} onBack={()=>{setWorkflowId(undefined);setPage('dashboard')}}/>; return <div className="app-shell"><Sidebar page={page} setPage={p=>{setPage(p);if(p!=='workflows')setWorkflowId(undefined)}}/><main className="main">{page==='dashboard'&&<Dashboard openWorkflow={(id)=>{setWorkflowId(id);setPage('workflows')}}/>}{page==='workflows'&&<WorkflowBuilder onBack={()=>setPage('dashboard')}/>} {page==='executions'&&<Placeholder title="Execution center" copy="Run history and real-time traces will appear here as workflows execute."/>}{page==='integrations'&&<Placeholder title="Integrations" copy="Connect Slack, Discord, SMTP and external APIs from this workspace."/>}{page==='analytics'&&<Placeholder title="Analytics" copy="Workflow performance, failure rates and automation savings will live here."/>}</main></div>}
function Placeholder({title,copy}:{title:string;copy:string}){return <div className="placeholder"><div className="eyebrow">FLOWFORGE</div><h1>{title}</h1><p>{copy}</p></div>}
