import{j as e,c}from"./utils-vy3jnSxZ.js";import{r as l}from"./iframe-Cuyv_Mtc.js";import{c as u}from"./index-CpxX1EO1.js";import{B as N}from"./Button-CVTKEBpS.js";import"./preload-helper-PPVm8Dsz.js";const j=u("rounded-lg border bg-card text-card-foreground",{variants:{variant:{default:"shadow-sm",interactive:"shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer",elevated:"shadow-md",flat:"shadow-none border-transparent"}},defaultVariants:{variant:"default"}}),s=l.forwardRef(({className:a,variant:r,...t},v)=>e.jsx("div",{ref:v,className:c(j({variant:r,className:a})),...t}));s.displayName="Card";const d=l.forwardRef(({className:a,...r},t)=>e.jsx("div",{ref:t,className:c("flex flex-col space-y-1.5 p-6",a),...r}));d.displayName="CardHeader";const n=l.forwardRef(({className:a,...r},t)=>e.jsx("h3",{ref:t,className:c("text-2xl font-semibold leading-none tracking-tight",a),...r}));n.displayName="CardTitle";const o=l.forwardRef(({className:a,...r},t)=>e.jsx("p",{ref:t,className:c("text-sm text-muted-foreground",a),...r}));o.displayName="CardDescription";const i=l.forwardRef(({className:a,...r},t)=>e.jsx("div",{ref:t,className:c("p-6 pt-0",a),...r}));i.displayName="CardContent";const f=l.forwardRef(({className:a,...r},t)=>e.jsx("div",{ref:t,className:c("flex items-center p-6 pt-0",a),...r}));f.displayName="CardFooter";s.__docgenInfo={description:"",methods:[],displayName:"Card",composes:["HTMLAttributes","VariantProps"]};d.__docgenInfo={description:"",methods:[],displayName:"CardHeader"};n.__docgenInfo={description:"",methods:[],displayName:"CardTitle"};o.__docgenInfo={description:"",methods:[],displayName:"CardDescription"};i.__docgenInfo={description:"",methods:[],displayName:"CardContent"};f.__docgenInfo={description:"",methods:[],displayName:"CardFooter"};const y={title:"UI/Card",component:s,argTypes:{variant:{control:"select",options:["default","interactive","elevated","flat"]}}},m={render:a=>e.jsxs(s,{...a,className:"w-[350px]",children:[e.jsxs(d,{children:[e.jsx(n,{children:"Card Title"}),e.jsx(o,{children:"Card description with supporting text."})]}),e.jsx(i,{children:e.jsx("p",{className:"text-sm",children:"Card content goes here. This is a default card with a subtle shadow."})}),e.jsx(f,{children:e.jsx(N,{size:"sm",children:"Action"})})]})},p={render:()=>e.jsxs(s,{variant:"interactive",className:"w-[350px]",children:[e.jsxs(d,{children:[e.jsx(n,{children:"Interactive Card"}),e.jsx(o,{children:"Hover over me to see the lift effect."})]}),e.jsx(i,{children:e.jsx("p",{className:"text-sm",children:"This card has hover shadow and cursor pointer for clickable items."})})]})},C={render:()=>e.jsxs(s,{variant:"elevated",className:"w-[350px]",children:[e.jsxs(d,{children:[e.jsx(n,{children:"Elevated Card"}),e.jsx(o,{children:"A card with more prominent shadow."})]}),e.jsx(i,{children:e.jsx("p",{className:"text-sm",children:"Use this variant to draw attention to important content."})})]})},x={render:()=>e.jsxs(s,{variant:"flat",className:"w-[350px]",children:[e.jsxs(d,{children:[e.jsx(n,{children:"Flat Card"}),e.jsx(o,{children:"No shadow, no border."})]}),e.jsx(i,{children:e.jsx("p",{className:"text-sm",children:"Use this variant for nested cards or subtle containers."})})]})},h={render:()=>e.jsx("div",{className:"grid grid-cols-2 gap-4",children:["default","interactive","elevated","flat"].map(a=>e.jsxs(s,{variant:a,className:"w-[280px]",children:[e.jsxs(d,{children:[e.jsx(n,{className:"text-base",children:a}),e.jsxs(o,{children:["Variant: ",a]})]}),e.jsx(i,{children:e.jsx("p",{className:"text-sm text-muted-foreground",children:"Hover to compare effects."})})]},a))})};m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  render: args => <Card {...args} className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description with supporting text.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Card content goes here. This is a default card with a subtle shadow.</p>
      </CardContent>
      <CardFooter>
        <Button size="sm">Action</Button>
      </CardFooter>
    </Card>
}`,...m.parameters?.docs?.source}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  render: () => <Card variant="interactive" className="w-[350px]">
      <CardHeader>
        <CardTitle>Interactive Card</CardTitle>
        <CardDescription>Hover over me to see the lift effect.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">This card has hover shadow and cursor pointer for clickable items.</p>
      </CardContent>
    </Card>
}`,...p.parameters?.docs?.source}}};C.parameters={...C.parameters,docs:{...C.parameters?.docs,source:{originalSource:`{
  render: () => <Card variant="elevated" className="w-[350px]">
      <CardHeader>
        <CardTitle>Elevated Card</CardTitle>
        <CardDescription>A card with more prominent shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Use this variant to draw attention to important content.</p>
      </CardContent>
    </Card>
}`,...C.parameters?.docs?.source}}};x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  render: () => <Card variant="flat" className="w-[350px]">
      <CardHeader>
        <CardTitle>Flat Card</CardTitle>
        <CardDescription>No shadow, no border.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Use this variant for nested cards or subtle containers.</p>
      </CardContent>
    </Card>
}`,...x.parameters?.docs?.source}}};h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-2 gap-4">
      {(['default', 'interactive', 'elevated', 'flat'] as const).map(variant => <Card key={variant} variant={variant} className="w-[280px]">
          <CardHeader>
            <CardTitle className="text-base">{variant}</CardTitle>
            <CardDescription>Variant: {variant}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Hover to compare effects.</p>
          </CardContent>
        </Card>)}
    </div>
}`,...h.parameters?.docs?.source}}};const D=["Default","Interactive","Elevated","Flat","AllVariants"];export{h as AllVariants,m as Default,C as Elevated,x as Flat,p as Interactive,D as __namedExportsOrder,y as default};
