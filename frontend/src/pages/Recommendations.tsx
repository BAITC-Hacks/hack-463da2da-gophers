import { useState } from 'react'
const item={title:'System Design: от Middle к Senior',factors:['Критичный навык System Design для следующего грейда','Разрыв: текущий уровень 2 из требуемых 4','Шаг соответствует траектории Middle → Senior']}
export function Recommendations(){const[done,setDone]=useState(false);return <section><h2>Рекомендованный шаг</h2><article className={done?'recommendation done':'recommendation'}><h3>{item.title}</h3><p>Этот шаг сильнее всего приблизит вас к следующему уровню.</p><ul>{item.factors.map(x=><li key={x}>{x}</li>)}</ul><button onClick={()=>setDone(true)} disabled={done}>{done?'✓ Выполнено — System Design: 2 → 3':'Отметить выполненным'}</button></article></section>}

