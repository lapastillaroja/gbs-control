// Exercise the actual profile UI controller with mock DOM/network; no browser dependency.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../webui.html'), 'utf8');
const code = html.slice(html.indexOf('const init24kProfiles ='), html.indexOf('const initUI ='));
async function fixture(behavior = 'success') {
  const elements = {};
  for (const id of ['profile24k','apply24kProfile','profile24kStatus'])
    elements[id] = {value:'0', textContent:'', disabled:false, listeners:{},
      options:[{text:'standard'},{text:'MS9'},{text:'Toei'},{text:'4:3 Toei'}],
      addEventListener(event, fn) { this.listeners[event] = fn; }};
  let state = {selected:2, active:true, pending:false, saved:true, component:false};
  const posts = [];
  const context = {document:{getElementById:id=>elements[id]}, URLSearchParams,
    setInterval:()=>0, setTimeout:fn=>{fn();return 0;},
    fetch:async (url, options={}) => {
      assert.equal(url, '/profiles/24k');
      if (options.method === 'POST') {
        posts.push(options.body.toString());
        if (behavior==='reject') return {ok:false,text:async()=> 'profile request pending'};
        const selected = Number(options.body.get('profile'));
        state={...state, selected, active:behavior==='success', pending:behavior==='timeout', saved:behavior!=='savefail'};
      }
      return {ok:true,json:async()=>state};
    }};
  vm.runInNewContext(code+'\ninit24kProfiles();',context);
  await new Promise(setImmediate);
  return {elements,posts};
}
(async()=>{
  let f=await fixture(); const s=f.elements.profile24k,b=f.elements.apply24kProfile,t=f.elements.profile24kStatus;
  assert.equal(s.value,'2');assert.match(t.textContent,/active/);
  s.value='1';s.listeners.change();assert.equal(f.posts.length,0);assert.match(t.textContent,/Not applied/);
  await b.listeners.click();assert.deepEqual(f.posts,['profile=1']);assert.match(t.textContent,/active/);assert.equal(b.disabled,false);
  s.value='3';s.listeners.change();await b.listeners.click();
  assert.deepEqual(f.posts,['profile=1','profile=3']);assert.match(t.textContent,/active/);
  for(const [behavior,message] of [['reject',/request pending/],['timeout',/Could not confirm/],['savefail',/saving failed/]]) {
    f=await fixture(behavior);await f.elements.apply24kProfile.listeners.click();
    assert.match(f.elements.profile24kStatus.textContent,message);
    assert.equal(f.elements.apply24kProfile.disabled,false);assert.equal(f.elements.profile24k.disabled,false);
  }
  console.log('Profile UI: saved selection, explicit apply, rejected request, timeout and save failure passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
