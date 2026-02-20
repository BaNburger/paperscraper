import{j as e}from"./utils-vy3jnSxZ.js";import{D as o,f as n,a as t,b as r,c as l,d as s,e as c}from"./Dialog-BFu2uZap.js";import{B as i}from"./Button-CVTKEBpS.js";import{L as d,I as p}from"./Label-CIXShTps.js";import"./iframe-Cuyv_Mtc.js";import"./preload-helper-PPVm8Dsz.js";import"./index-j9kV39G_.js";import"./x-BUlYV1nc.js";import"./index-CpxX1EO1.js";const f={title:"UI/Dialog",component:o},a={render:()=>e.jsxs(o,{children:[e.jsx(n,{asChild:!0,children:e.jsx(i,{variant:"outline",children:"Open Dialog"})}),e.jsxs(t,{children:[e.jsxs(r,{children:[e.jsx(l,{children:"Dialog Title"}),e.jsx(s,{children:"This is a dialog description. It provides context about the action."})]}),e.jsx("div",{className:"space-y-4 py-4",children:e.jsxs("div",{className:"space-y-2",children:[e.jsx(d,{htmlFor:"name",children:"Name"}),e.jsx(p,{id:"name",placeholder:"Enter your name"})]})}),e.jsxs(c,{children:[e.jsx(i,{variant:"outline",children:"Cancel"}),e.jsx(i,{children:"Save"})]})]})]})};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>
            This is a dialog description. It provides context about the action.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" placeholder="Enter your name" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
}`,...a.parameters?.docs?.source}}};const y=["Default"];export{a as Default,y as __namedExportsOrder,f as default};
