import{j as a,c as x}from"./utils-vy3jnSxZ.js";import{r as N}from"./iframe-Cuyv_Mtc.js";import{c,B as f}from"./Button-CVTKEBpS.js";import{P as s}from"./plus-C_ZX4cZG.js";import{X as w}from"./x-BUlYV1nc.js";import{T as m}from"./trash-2-CRetKRaF.js";import"./preload-helper-PPVm8Dsz.js";import"./index-CpxX1EO1.js";const b=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915",key:"1i5ecw"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}]],d=c("settings",b);const j=[["path",{d:"M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7",key:"1m0v6g"}],["path",{d:"M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z",key:"ohrbg2"}]],u=c("square-pen",j),I={sm:"icon-sm",default:"icon",lg:"icon-lg"},e=N.forwardRef(({size:p="default",className:h,...g},v)=>a.jsx(f,{ref:v,size:I[p],className:x("shrink-0",h),...g}));e.displayName="IconButton";e.__docgenInfo={description:"",methods:[],displayName:"IconButton",props:{size:{required:!1,tsType:{name:"union",raw:"'sm' | 'default' | 'lg'",elements:[{name:"literal",value:"'sm'"},{name:"literal",value:"'default'"},{name:"literal",value:"'lg'"}]},description:"",defaultValue:{value:"'default'",computed:!1}},"aria-label":{required:!0,tsType:{name:"string"},description:""}},composes:["Omit"]};const A={title:"UI/IconButton",component:e,argTypes:{variant:{control:"select",options:["default","destructive","outline","secondary","ghost"]},size:{control:"select",options:["sm","default","lg"]}}},t={args:{"aria-label":"Add item",children:a.jsx(s,{className:"h-4 w-4"})}},r={args:{variant:"ghost","aria-label":"Settings",children:a.jsx(d,{className:"h-4 w-4"})}},l={args:{variant:"destructive","aria-label":"Delete item",children:a.jsx(m,{className:"h-4 w-4"})}},n={args:{size:"sm",variant:"outline","aria-label":"Edit",children:a.jsx(u,{className:"h-3.5 w-3.5"})}},i={render:()=>a.jsxs("div",{className:"flex items-center gap-2",children:[a.jsx(e,{"aria-label":"Add",variant:"default",children:a.jsx(s,{className:"h-4 w-4"})}),a.jsx(e,{"aria-label":"Edit",variant:"outline",children:a.jsx(u,{className:"h-4 w-4"})}),a.jsx(e,{"aria-label":"Settings",variant:"secondary",children:a.jsx(d,{className:"h-4 w-4"})}),a.jsx(e,{"aria-label":"Close",variant:"ghost",children:a.jsx(w,{className:"h-4 w-4"})}),a.jsx(e,{"aria-label":"Delete",variant:"destructive",children:a.jsx(m,{className:"h-4 w-4"})})]})},o={render:()=>a.jsxs("div",{className:"flex items-center gap-2",children:[a.jsx(e,{size:"sm",variant:"outline","aria-label":"Small",children:a.jsx(s,{className:"h-3.5 w-3.5"})}),a.jsx(e,{size:"default",variant:"outline","aria-label":"Default",children:a.jsx(s,{className:"h-4 w-4"})}),a.jsx(e,{size:"lg",variant:"outline","aria-label":"Large",children:a.jsx(s,{className:"h-5 w-5"})})]})};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    'aria-label': 'Add item',
    children: <Plus className="h-4 w-4" />
  }
}`,...t.parameters?.docs?.source}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'ghost',
    'aria-label': 'Settings',
    children: <Settings className="h-4 w-4" />
  }
}`,...r.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'destructive',
    'aria-label': 'Delete item',
    children: <Trash2 className="h-4 w-4" />
  }
}`,...l.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'sm',
    variant: 'outline',
    'aria-label': 'Edit',
    children: <Edit className="h-3.5 w-3.5" />
  }
}`,...n.parameters?.docs?.source}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <IconButton aria-label="Add" variant="default"><Plus className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Edit" variant="outline"><Edit className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Settings" variant="secondary"><Settings className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Close" variant="ghost"><X className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Delete" variant="destructive"><Trash2 className="h-4 w-4" /></IconButton>
    </div>
}`,...i.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-2">
      <IconButton size="sm" variant="outline" aria-label="Small"><Plus className="h-3.5 w-3.5" /></IconButton>
      <IconButton size="default" variant="outline" aria-label="Default"><Plus className="h-4 w-4" /></IconButton>
      <IconButton size="lg" variant="outline" aria-label="Large"><Plus className="h-5 w-5" /></IconButton>
    </div>
}`,...o.parameters?.docs?.source}}};const T=["Default","Ghost","Destructive","Small","AllVariants","Sizes"];export{i as AllVariants,t as Default,l as Destructive,r as Ghost,o as Sizes,n as Small,T as __namedExportsOrder,A as default};
