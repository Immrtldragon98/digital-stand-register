export type FeedbackForm = {kind: "BUG" | "SUGGESTION"; title: string; description: string; page: string; reporter: string};
export type FeedbackPayload = FeedbackForm & {request_id: string};
export type FeedbackDraft = {form: FeedbackForm; pending: FeedbackPayload | null};
export const emptyFeedback: FeedbackForm = {kind:"BUG", title:"", description:"", page:"", reporter:""};
const limits = {title:160, description:5000, page:200, reporter:80};
function validForm(value:any): value is FeedbackForm {
  return !!value && ["BUG","SUGGESTION"].includes(value.kind) && Object.entries(limits).every(([key,max])=>typeof value[key]==="string" && value[key].length<=max);
}
function validPayload(value:any): value is FeedbackPayload {
  const requestId=value?.request_id;
  return validForm(value) && typeof requestId==="string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(requestId);
}
const key = (base:string)=>`dsr-feedback-draft:${base}`;
export function loadFeedbackDraft(storage: Pick<Storage,"getItem">, base:string): FeedbackDraft|null {
  try {
    const raw=storage.getItem(key(base)); if(!raw || raw.length>26000)return null;
    const value=JSON.parse(raw); if(!validForm(value.form))return null;
    const pending=value.pending;
    const same=validPayload(pending) && (["kind",...Object.keys(limits)] as (keyof FeedbackForm)[]).every(field=>pending[field]===value.form[field]);
    return {form:value.form,pending:same?pending:null};
  }catch{return null;}
}
export function saveFeedbackDraft(storage: Pick<Storage,"setItem">, base:string, draft:FeedbackDraft):boolean {
  try {storage.setItem(key(base),JSON.stringify(draft));return true;}catch{return false;}
}
export function clearFeedbackDraft(storage: Pick<Storage,"removeItem">, base:string) {
  try {storage.removeItem(key(base));}catch{/* The form can still be cleared in memory. */}
}
