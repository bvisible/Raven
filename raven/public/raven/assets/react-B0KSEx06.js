import{a as e}from"./rolldown-runtime-BWaJ3C7D.js";import{r as t}from"./jsx-runtime-Ddz-2cRL.js";import{n,r}from"./vanilla-CkNQ_Qr6.js";var i=e(t(),1),a=(0,i.createContext)(void 0);function o(e){let t=(0,i.useContext)(a);return(e==null?void 0:e.store)||t||n()}var s=e=>typeof(e==null?void 0:e.then)==`function`,c=e=>{e.status||(e.status=`pending`,e.then(t=>{e.status=`fulfilled`,e.value=t},t=>{e.status=`rejected`,e.reason=t}))},l=i.use||(e=>{if(e.status===`pending`)throw e;if(e.status===`fulfilled`)return e.value;throw e.status===`rejected`?e.reason:(c(e),e)}),u=new WeakMap,d=(e,t,n)=>{let i=r(e),a=i[26],o=u.get(t);return o||(o=new Promise((r,c)=>{let l=t,d=e=>t=>{l===e&&r(t)},f=e=>t=>{l===e&&c(t)},p=()=>{try{let t=n();s(t)?(u.set(t,o),l=t,t.then(d(t),f(t)),a(i,e,t,p)):r(t)}catch(e){c(e)}};t.then(d(t),f(t)),a(i,e,t,p)}),u.set(t,o)),o};function f(e,t){let{delay:n,unstable_promiseStatus:r=!i.use}=t||{},a=o(t),[[u,f,p],m]=(0,i.useReducer)(t=>{let n=a.get(e);return Object.is(t[0],n)&&t[1]===a&&t[2]===e?t:[n,a,e]},void 0,()=>[a.get(e),a,e]),h=u;if((f!==a||p!==e)&&(m(),h=a.get(e)),(0,i.useEffect)(()=>{let t=a.sub(e,()=>{if(r)try{let t=a.get(e);s(t)&&c(d(a,t,()=>a.get(e)))}catch(e){}typeof n==`number`?(console.warn(`[DEPRECATED] delay option is deprecated and will be removed in v3.

Migration guide:

Create a custom hook like the following.

function useAtomValueWithDelay<Value>(
  atom: Atom<Value>,
  options: { delay: number },
): Value {
  const { delay } = options
  const store = useStore(options)
  const [value, setValue] = useState(() => store.get(atom))
  useEffect(() => {
    const unsub = store.sub(atom, () => {
      setTimeout(() => setValue(store.get(atom)), delay)
    })
    return unsub
  }, [store, atom, delay])
  return value
}
`),setTimeout(m,n)):m()});return m(),t},[a,e,n,r]),(0,i.useDebugValue)(h),s(h)){let t=d(a,h,()=>a.get(e));return r&&c(t),l(t)}return h}function p(e,t){let n=o(t);return(0,i.useCallback)((...t)=>n.set(e,...t),[n,e])}function m(e,t){return[f(e,t),p(e,t)]}export{f as n,p as r,m as t};