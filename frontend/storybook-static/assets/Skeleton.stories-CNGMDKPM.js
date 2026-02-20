import{j as e,c as m}from"./utils-vy3jnSxZ.js";function s({className:a}){return e.jsx("div",{className:m("rounded-md bg-muted bg-gradient-to-r from-muted via-muted-foreground/5 to-muted bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]",a)})}function l({className:a}){return e.jsxs("div",{className:m("rounded-lg border bg-card p-6 space-y-4",a),children:[e.jsx(s,{className:"h-6 w-3/4"}),e.jsx(s,{className:"h-4 w-full"}),e.jsx(s,{className:"h-4 w-5/6"}),e.jsxs("div",{className:"flex gap-2 pt-2",children:[e.jsx(s,{className:"h-8 w-20"}),e.jsx(s,{className:"h-8 w-20"})]})]})}function i(){return e.jsx("div",{className:"grid gap-4 md:grid-cols-2 lg:grid-cols-4",children:Array.from({length:4}).map((a,d)=>e.jsxs("div",{className:"rounded-lg border bg-card p-6",children:[e.jsx(s,{className:"h-4 w-1/2 mb-2"}),e.jsx(s,{className:"h-8 w-3/4"})]},d))})}s.__docgenInfo={description:"",methods:[],displayName:"Skeleton",props:{className:{required:!1,tsType:{name:"string"},description:""}}};l.__docgenInfo={description:"",methods:[],displayName:"SkeletonCard",props:{className:{required:!1,tsType:{name:"string"},description:""}}};i.__docgenInfo={description:"",methods:[],displayName:"SkeletonStats"};const x={title:"UI/Skeleton",component:s},r={render:()=>e.jsxs("div",{className:"space-y-3 w-[300px]",children:[e.jsx(s,{className:"h-4 w-3/4"}),e.jsx(s,{className:"h-4 w-full"}),e.jsx(s,{className:"h-4 w-5/6"})]})},n={render:()=>e.jsx("div",{className:"w-[400px]",children:e.jsx(l,{})})},t={render:()=>e.jsx(i,{})},c={render:()=>e.jsxs("div",{className:"flex items-center gap-3",children:[e.jsx(s,{className:"h-10 w-10 rounded-full"}),e.jsxs("div",{className:"space-y-2",children:[e.jsx(s,{className:"h-4 w-[200px]"}),e.jsx(s,{className:"h-3 w-[150px]"})]})]})},o={render:()=>e.jsx("div",{className:"space-y-4 w-[500px]",children:Array.from({length:3}).map((a,d)=>e.jsx(l,{},d))})};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-3 w-[300px]">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
    </div>
}`,...r.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  render: () => <div className="w-[400px]">
      <SkeletonCard />
    </div>
}`,...n.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  render: () => <SkeletonStats />
}`,...t.parameters?.docs?.source}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-[200px]" />
        <Skeleton className="h-3 w-[150px]" />
      </div>
    </div>
}`,...c.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 w-[500px]">
      {Array.from({
      length: 3
    }).map((_, i) => <SkeletonCard key={i} />)}
    </div>
}`,...o.parameters?.docs?.source}}};const u=["Default","CardSkeleton","StatsSkeleton","AvatarAndText","ListSkeleton"];export{c as AvatarAndText,n as CardSkeleton,r as Default,o as ListSkeleton,t as StatsSkeleton,u as __namedExportsOrder,x as default};
