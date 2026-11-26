export function matchingPositions(lines:any[],query:string){
 const tokens=query.toLowerCase().trim().split(/\s+/).filter(Boolean);
 return lines.flatMap(line=>(line.positions||[]).map((position:any)=>({line,position}))).filter(({line,position})=>tokens.every(token=>`${line.name} p${position.position_number} ${position.current_stand?.code||"empty"}`.toLowerCase().includes(token)));
}
export function selectionFromLocation(lines:any[],search:string){
 const params=new URLSearchParams(search),matches=matchingPositions(lines,params.get("q")||"");
 const line=lines.find(row=>row.name===params.get("line"))||matches[0]?.line||lines[0]||null;
 const position=line?.positions?.find((row:any)=>String(row.position_number)===params.get("position"))||null;
 return {line,position,query:params.get("q")||""};
}
