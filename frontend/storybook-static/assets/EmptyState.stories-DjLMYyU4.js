import{j as e,c as u}from"./utils-vy3jnSxZ.js";import"./iframe-Cuyv_Mtc.js";import{c as o,B as n}from"./Button-CVTKEBpS.js";import"./preload-helper-PPVm8Dsz.js";import"./index-CpxX1EO1.js";const h=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",key:"1oefj6"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5",key:"wfsgrz"}],["path",{d:"M10 9H8",key:"b1mrlr"}],["path",{d:"M16 13H8",key:"t4e002"}],["path",{d:"M16 17H8",key:"z1uh3a"}]],y=o("file-text",h);const g=[["polyline",{points:"22 12 16 12 14 15 10 15 8 12 2 12",key:"o97t9d"}],["path",{d:"M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",key:"oot6mr"}]],f=o("inbox",g);const x=[["path",{d:"m21 21-4.34-4.34",key:"14j7rj"}],["circle",{cx:"11",cy:"11",r:"8",key:"4ej97u"}]],k=o("search",x);function c({icon:l,title:p,description:d,action:t,secondaryAction:r,className:m}){return e.jsxs("div",{className:u("flex flex-col items-center justify-center py-12 text-center",m),children:[e.jsx("div",{className:"w-16 h-16 mb-4 text-muted-foreground flex items-center justify-center",children:l}),e.jsx("h3",{className:"text-lg font-semibold mb-2",children:p}),e.jsx("p",{className:"text-muted-foreground mb-6 max-w-sm",children:d}),(t||r)&&e.jsxs("div",{className:"flex gap-3",children:[t&&e.jsx(n,{onClick:t.onClick,children:t.label}),r&&e.jsx(n,{variant:"outline",onClick:r.onClick,children:r.label})]})]})}c.__docgenInfo={description:"",methods:[],displayName:"EmptyState",props:{icon:{required:!0,tsType:{name:"ReactNode"},description:""},title:{required:!0,tsType:{name:"string"},description:""},description:{required:!0,tsType:{name:"string"},description:""},action:{required:!1,tsType:{name:"signature",type:"object",raw:`{
  label: string
  onClick: () => void
}`,signature:{properties:[{key:"label",value:{name:"string",required:!0}},{key:"onClick",value:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}},required:!0}}]}},description:""},secondaryAction:{required:!1,tsType:{name:"signature",type:"object",raw:`{
  label: string
  onClick: () => void
}`,signature:{properties:[{key:"label",value:{name:"string",required:!0}},{key:"onClick",value:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}},required:!0}}]}},description:""},className:{required:!1,tsType:{name:"string"},description:""}}};const C={title:"UI/EmptyState",component:c},a={args:{icon:e.jsx(y,{className:"h-16 w-16"}),title:"No papers yet",description:"Get started by importing your first paper from DOI, PDF, or a database.",action:{label:"Import Papers",onClick:()=>{}}}},s={args:{icon:e.jsx(k,{className:"h-16 w-16"}),title:"No search results",description:"Try adjusting your search terms or filters.",action:{label:"Clear Search",onClick:()=>{}},secondaryAction:{label:"Browse All",onClick:()=>{}}}},i={args:{icon:e.jsx(f,{className:"h-16 w-16"}),title:"All caught up",description:"You have no new notifications at this time."}};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    icon: <FileText className="h-16 w-16" />,
    title: 'No papers yet',
    description: 'Get started by importing your first paper from DOI, PDF, or a database.',
    action: {
      label: 'Import Papers',
      onClick: () => {}
    }
  }
}`,...a.parameters?.docs?.source}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    icon: <Search className="h-16 w-16" />,
    title: 'No search results',
    description: 'Try adjusting your search terms or filters.',
    action: {
      label: 'Clear Search',
      onClick: () => {}
    },
    secondaryAction: {
      label: 'Browse All',
      onClick: () => {}
    }
  }
}`,...s.parameters?.docs?.source}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    icon: <Inbox className="h-16 w-16" />,
    title: 'All caught up',
    description: 'You have no new notifications at this time.'
  }
}`,...i.parameters?.docs?.source}}};const A=["WithAction","WithTwoActions","WithoutAction"];export{a as WithAction,s as WithTwoActions,i as WithoutAction,A as __namedExportsOrder,C as default};
