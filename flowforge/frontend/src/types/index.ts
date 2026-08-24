export type Workflow = { id:string; owner_id:string; name:string; description:string; enabled:boolean; nodes:any[]; edges:any[]; created_at:string; updated_at:string; };
export type Execution = { id:string; workflow_id:string; status:string; input_json:any; output_json:any; error:string; duration_ms:number; started_at?:string; finished_at?:string; };
