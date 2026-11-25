export function plantDate(date:Date=new Date()):string{
 const parts=new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Kolkata",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(date);
 const value=(type:string)=>parts.find(part=>part.type===type)?.value||"";
 return `${value("year")}-${value("month")}-${value("day")}`;
}
