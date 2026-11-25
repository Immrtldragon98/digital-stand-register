const keys = new Map<string,string>();
export function confirmationKey(scope:string, body:string){
 const signature=`${scope}:${body}`;
 const existing=keys.get(signature);if(existing)return existing;
 const key=`${scope}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
 if(keys.size>=20)keys.delete(keys.keys().next().value!);
 keys.set(signature,key);return key;
}

export function forgetConfirmationKey(scope:string,body:string){keys.delete(`${scope}:${body}`);}
