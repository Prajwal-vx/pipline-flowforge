import { ArrowUpRight } from 'lucide-react';
export default function StatCard({label,value,sub}:{label:string;value:string|number;sub:string}){return <div className="stat-card"><div className="stat-top"><span>{label}</span><ArrowUpRight size={15}/></div><div className="stat-value">{value}</div><div className="stat-sub">{sub}</div></div>}
