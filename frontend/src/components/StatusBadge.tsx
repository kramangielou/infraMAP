import type {Status} from '../types';export function StatusBadge({status}:{status:Status}){return <span className={`status ${status}`}><span aria-hidden="true">●</span>{status}</span>}
