import{j as e}from"./utils-vy3jnSxZ.js";import{I as r,L as p}from"./Label-CIXShTps.js";import"./iframe-Cuyv_Mtc.js";import"./preload-helper-PPVm8Dsz.js";const i={title:"UI/Input",component:r},a={args:{placeholder:"Enter text..."}},s={render:()=>e.jsxs("div",{className:"space-y-2 w-[300px]",children:[e.jsx(p,{htmlFor:"email",children:"Email"}),e.jsx(r,{id:"email",type:"email",placeholder:"you@example.com"})]})},l={render:()=>e.jsx("div",{className:"w-[300px]",children:e.jsx(r,{placeholder:"Email",error:"Please enter a valid email address"})})},t={args:{disabled:!0,value:"Disabled input"}},o={render:()=>e.jsxs("div",{className:"space-y-3 w-[300px]",children:[e.jsx(r,{type:"text",placeholder:"Text"}),e.jsx(r,{type:"email",placeholder:"Email"}),e.jsx(r,{type:"password",placeholder:"Password"}),e.jsx(r,{type:"number",placeholder:"Number"}),e.jsx(r,{type:"search",placeholder:"Search..."})]})};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...a.parameters?.docs?.source}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-2 w-[300px]">
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" placeholder="you@example.com" />
    </div>
}`,...s.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  render: () => <div className="w-[300px]">
      <Input placeholder="Email" error="Please enter a valid email address" />
    </div>
}`,...l.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    disabled: true,
    value: 'Disabled input'
  }
}`,...t.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-3 w-[300px]">
      <Input type="text" placeholder="Text" />
      <Input type="email" placeholder="Email" />
      <Input type="password" placeholder="Password" />
      <Input type="number" placeholder="Number" />
      <Input type="search" placeholder="Search..." />
    </div>
}`,...o.parameters?.docs?.source}}};const u=["Default","WithLabel","WithError","Disabled","Types"];export{a as Default,t as Disabled,o as Types,l as WithError,s as WithLabel,u as __namedExportsOrder,i as default};
