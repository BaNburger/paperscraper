import{j as r}from"./utils-vy3jnSxZ.js";import{c as j,B as e}from"./Button-CVTKEBpS.js";import{P as z}from"./plus-C_ZX4cZG.js";import{T as f}from"./trash-2-CRetKRaF.js";import"./iframe-Cuyv_Mtc.js";import"./preload-helper-PPVm8Dsz.js";import"./index-CpxX1EO1.js";const w=[["path",{d:"M12 15V3",key:"m9g1x1"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4",key:"ih7n3h"}],["path",{d:"m7 10 5 5 5-5",key:"brsn70"}]],D=j("download",w),O={title:"UI/Button",component:e,argTypes:{variant:{control:"select",options:["default","destructive","outline","secondary","ghost","link","success","warning"]},size:{control:"select",options:["xs","sm","default","lg","icon","icon-sm"]}}},s={args:{children:"Button"}},a={args:{variant:"destructive",children:"Delete"}},n={args:{variant:"outline",children:"Outline"}},t={args:{variant:"secondary",children:"Secondary"}},o={args:{variant:"ghost",children:"Ghost"}},c={args:{variant:"link",children:"Link"}},i={args:{variant:"success",children:"Approve"}},l={args:{variant:"warning",children:"Caution"}},d={args:{size:"sm",children:"Small"}},u={args:{size:"xs",children:"Tiny"}},m={args:{size:"lg",children:"Large"}},p={args:{size:"icon",variant:"outline",children:r.jsx(f,{className:"h-4 w-4"})}},g={args:{size:"icon-sm",variant:"ghost",children:r.jsx(z,{className:"h-4 w-4"})}},h={args:{isLoading:!0,children:"Saving..."}},v={args:{disabled:!0,children:"Disabled"}},S={args:{children:r.jsxs(r.Fragment,{children:[r.jsx(D,{className:"h-4 w-4"})," Export"]})}},x={render:()=>r.jsxs("div",{className:"flex flex-wrap gap-3",children:[r.jsx(e,{children:"Default"}),r.jsx(e,{variant:"secondary",children:"Secondary"}),r.jsx(e,{variant:"outline",children:"Outline"}),r.jsx(e,{variant:"ghost",children:"Ghost"}),r.jsx(e,{variant:"destructive",children:"Destructive"}),r.jsx(e,{variant:"success",children:"Success"}),r.jsx(e,{variant:"warning",children:"Warning"}),r.jsx(e,{variant:"link",children:"Link"})]})},B={render:()=>r.jsxs("div",{className:"flex items-center gap-3",children:[r.jsx(e,{size:"xs",children:"XS"}),r.jsx(e,{size:"sm",children:"SM"}),r.jsx(e,{size:"default",children:"Default"}),r.jsx(e,{size:"lg",children:"LG"}),r.jsx(e,{size:"icon",children:r.jsx(z,{className:"h-4 w-4"})}),r.jsx(e,{size:"icon-sm",children:r.jsx(z,{className:"h-4 w-4"})})]})};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Button'
  }
}`,...s.parameters?.docs?.source}}};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'destructive',
    children: 'Delete'
  }
}`,...a.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    children: 'Outline'
  }
}`,...n.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    children: 'Secondary'
  }
}`,...t.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'ghost',
    children: 'Ghost'
  }
}`,...o.parameters?.docs?.source}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'link',
    children: 'Link'
  }
}`,...c.parameters?.docs?.source}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'success',
    children: 'Approve'
  }
}`,...i.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'warning',
    children: 'Caution'
  }
}`,...l.parameters?.docs?.source}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'sm',
    children: 'Small'
  }
}`,...d.parameters?.docs?.source}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'xs',
    children: 'Tiny'
  }
}`,...u.parameters?.docs?.source}}};m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'lg',
    children: 'Large'
  }
}`,...m.parameters?.docs?.source}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'icon',
    variant: 'outline',
    children: <Trash2 className="h-4 w-4" />
  }
}`,...p.parameters?.docs?.source}}};g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'icon-sm',
    variant: 'ghost',
    children: <Plus className="h-4 w-4" />
  }
}`,...g.parameters?.docs?.source}}};h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    isLoading: true,
    children: 'Saving...'
  }
}`,...h.parameters?.docs?.source}}};v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    disabled: true,
    children: 'Disabled'
  }
}`,...v.parameters?.docs?.source}}};S.parameters={...S.parameters,docs:{...S.parameters?.docs,source:{originalSource:`{
  args: {
    children: <><Download className="h-4 w-4" /> Export</>
  }
}`,...S.parameters?.docs?.source}}};x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-3">
      <Button>Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="success">Success</Button>
      <Button variant="warning">Warning</Button>
      <Button variant="link">Link</Button>
    </div>
}`,...x.parameters?.docs?.source}}};B.parameters={...B.parameters,docs:{...B.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Button size="xs">XS</Button>
      <Button size="sm">SM</Button>
      <Button size="default">Default</Button>
      <Button size="lg">LG</Button>
      <Button size="icon"><Plus className="h-4 w-4" /></Button>
      <Button size="icon-sm"><Plus className="h-4 w-4" /></Button>
    </div>
}`,...B.parameters?.docs?.source}}};const A=["Default","Destructive","Outline","Secondary","Ghost","Link","Success","Warning","Small","ExtraSmall","Large","Icon","IconSmall","Loading","Disabled","WithIcon","AllVariants","AllSizes"];export{B as AllSizes,x as AllVariants,s as Default,a as Destructive,v as Disabled,u as ExtraSmall,o as Ghost,p as Icon,g as IconSmall,m as Large,c as Link,h as Loading,n as Outline,t as Secondary,d as Small,i as Success,l as Warning,S as WithIcon,A as __namedExportsOrder,O as default};
