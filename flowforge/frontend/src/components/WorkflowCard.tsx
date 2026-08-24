import { GitBranch, MoreHorizontal, Play, Power } from 'lucide-react';
import type { Workflow } from '../types';
export default function WorkflowCard({workflow,onOpen,onRun,onToggle}:{workflow:Workflow;onOpen:()=>void;onRun:()=>void;onToggle:()=>void}){return <div className="workflow-card">
 <div className="wf-icon"><GitBranch size={17}/></div><div className="wf-body" onClick={onOpen}><div className="wf-title">{workflow.name}</div><div className="wf-desc">{workflow.description||'No description'}</div><div className="wf-meta"><span className={`dot ${workflow.enabled?'green':''}`}></span>{workflow.enabled?'Active':'Draft'} · {workflow.nodes.length} nodes</div></div>
 <div className="wf-actions"><button title="Run" onClick={onRun}><Play size={15}/></button><button title="Toggle" onClick={onToggle}><Power size={15}/></button><button><MoreHorizontal size={15}/></button></div>
 </div>}
