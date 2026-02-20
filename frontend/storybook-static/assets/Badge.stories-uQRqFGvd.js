import{j as e,c as v}from"./utils-vy3jnSxZ.js";import"./iframe-Cuyv_Mtc.js";import{c as x}from"./index-CpxX1EO1.js";import"./preload-helper-PPVm8Dsz.js";const f=x("inline-flex items-center rounded-full border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",{variants:{variant:{default:"border-transparent bg-primary text-primary-foreground",secondary:"border-transparent bg-secondary text-secondary-foreground",destructive:"border-transparent bg-destructive text-destructive-foreground",outline:"text-foreground",success:"border-transparent bg-green-100 text-green-800",warning:"border-transparent bg-amber-100 text-amber-800",novelty:"border-transparent bg-violet-100 text-violet-800",ip:"border-transparent bg-blue-100 text-blue-800",marketability:"border-transparent bg-emerald-100 text-emerald-800",feasibility:"border-transparent bg-amber-100 text-amber-800",commercialization:"border-transparent bg-pink-100 text-pink-800"},size:{sm:"px-2 py-0.5 text-[10px]",default:"px-2.5 py-0.5 text-xs",lg:"px-3 py-1 text-sm"}},defaultVariants:{variant:"default",size:"default"}});function a({className:g,variant:m,size:u,...p}){return e.jsx("div",{className:v(f({variant:m,size:u}),g),...p})}a.__docgenInfo={description:"",methods:[],displayName:"Badge",composes:["HTMLAttributes","VariantProps"]};const j={title:"UI/Badge",component:a,argTypes:{variant:{control:"select",options:["default","secondary","destructive","outline","success","warning","novelty","ip","marketability","feasibility","commercialization"]},size:{control:"select",options:["sm","default","lg"]}}},r={args:{children:"Badge"}},n={args:{variant:"secondary",children:"Secondary"}},t={args:{variant:"destructive",children:"Error"}},i={args:{variant:"outline",children:"Outline"}},s={args:{variant:"success",children:"Active"}},c={args:{variant:"warning",children:"Pending"}},o={render:()=>e.jsxs("div",{className:"flex flex-wrap gap-2",children:[e.jsx(a,{variant:"novelty",children:"Novelty"}),e.jsx(a,{variant:"ip",children:"IP Potential"}),e.jsx(a,{variant:"marketability",children:"Marketability"}),e.jsx(a,{variant:"feasibility",children:"Feasibility"}),e.jsx(a,{variant:"commercialization",children:"Commercialization"})]})},d={render:()=>e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(a,{size:"sm",children:"Small"}),e.jsx(a,{size:"default",children:"Default"}),e.jsx(a,{size:"lg",children:"Large"})]})},l={render:()=>e.jsxs("div",{className:"flex flex-wrap gap-2",children:[e.jsx(a,{children:"Default"}),e.jsx(a,{variant:"secondary",children:"Secondary"}),e.jsx(a,{variant:"destructive",children:"Destructive"}),e.jsx(a,{variant:"outline",children:"Outline"}),e.jsx(a,{variant:"success",children:"Success"}),e.jsx(a,{variant:"warning",children:"Warning"}),e.jsx(a,{variant:"novelty",children:"Novelty"}),e.jsx(a,{variant:"ip",children:"IP"}),e.jsx(a,{variant:"marketability",children:"Market"}),e.jsx(a,{variant:"feasibility",children:"Feasibility"}),e.jsx(a,{variant:"commercialization",children:"Commerc."})]})};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Badge'
  }
}`,...r.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    children: 'Secondary'
  }
}`,...n.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'destructive',
    children: 'Error'
  }
}`,...t.parameters?.docs?.source}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    children: 'Outline'
  }
}`,...i.parameters?.docs?.source}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'success',
    children: 'Active'
  }
}`,...s.parameters?.docs?.source}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'warning',
    children: 'Pending'
  }
}`,...c.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Badge variant="novelty">Novelty</Badge>
      <Badge variant="ip">IP Potential</Badge>
      <Badge variant="marketability">Marketability</Badge>
      <Badge variant="feasibility">Feasibility</Badge>
      <Badge variant="commercialization">Commercialization</Badge>
    </div>
}`,...o.parameters?.docs?.source}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <Badge size="sm">Small</Badge>
      <Badge size="default">Default</Badge>
      <Badge size="lg">Large</Badge>
    </div>
}`,...d.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="novelty">Novelty</Badge>
      <Badge variant="ip">IP</Badge>
      <Badge variant="marketability">Market</Badge>
      <Badge variant="feasibility">Feasibility</Badge>
      <Badge variant="commercialization">Commerc.</Badge>
    </div>
}`,...l.parameters?.docs?.source}}};const S=["Default","Secondary","Destructive","Outline","Success","Warning","ScoringDimensions","Sizes","AllVariants"];export{l as AllVariants,r as Default,t as Destructive,i as Outline,o as ScoringDimensions,n as Secondary,d as Sizes,s as Success,c as Warning,S as __namedExportsOrder,j as default};
