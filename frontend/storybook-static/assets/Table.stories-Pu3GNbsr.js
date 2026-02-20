import{j as e,c as s}from"./utils-vy3jnSxZ.js";import{r as o}from"./iframe-Cuyv_Mtc.js";import"./preload-helper-PPVm8Dsz.js";const n=o.forwardRef(({className:a,...l},t)=>e.jsx("div",{className:"relative w-full overflow-auto",children:e.jsx("table",{ref:t,className:s("w-full caption-bottom text-sm",a),...l})}));n.displayName="Table";const m=o.forwardRef(({className:a,...l},t)=>e.jsx("thead",{ref:t,className:s("[&_tr]:border-b",a),...l}));m.displayName="TableHeader";const b=o.forwardRef(({className:a,...l},t)=>e.jsx("tbody",{ref:t,className:s("[&_tr:last-child]:border-0",a),...l}));b.displayName="TableBody";const T=o.forwardRef(({className:a,...l},t)=>e.jsx("tfoot",{ref:t,className:s("border-t bg-muted/50 font-medium [&>tr]:last:border-b-0",a),...l}));T.displayName="TableFooter";const c=o.forwardRef(({className:a,...l},t)=>e.jsx("tr",{ref:t,className:s("border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",a),...l}));c.displayName="TableRow";const r=o.forwardRef(({className:a,...l},t)=>e.jsx("th",{ref:t,className:s("h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0",a),...l}));r.displayName="TableHead";const d=o.forwardRef(({className:a,...l},t)=>e.jsx("td",{ref:t,className:s("p-4 align-middle [&:has([role=checkbox])]:pr-0",a),...l}));d.displayName="TableCell";const p=o.forwardRef(({className:a,...l},t)=>e.jsx("caption",{ref:t,className:s("mt-4 text-sm text-muted-foreground",a),...l}));p.displayName="TableCaption";n.__docgenInfo={description:"",methods:[],displayName:"Table"};m.__docgenInfo={description:"",methods:[],displayName:"TableHeader"};b.__docgenInfo={description:"",methods:[],displayName:"TableBody"};T.__docgenInfo={description:"",methods:[],displayName:"TableFooter"};r.__docgenInfo={description:"",methods:[],displayName:"TableHead"};c.__docgenInfo={description:"",methods:[],displayName:"TableRow"};d.__docgenInfo={description:"",methods:[],displayName:"TableCell"};p.__docgenInfo={description:"",methods:[],displayName:"TableCaption"};const u={title:"UI/Table",component:n},x=[{id:"1",title:"Novel CRISPR Applications",source:"PubMed",score:8.4,date:"2025-12-01"},{id:"2",title:"Quantum Computing Advances",source:"arXiv",score:7.9,date:"2025-11-15"},{id:"3",title:"mRNA Delivery Systems",source:"OpenAlex",score:9.1,date:"2025-10-20"},{id:"4",title:"Solid-State Batteries",source:"DOI",score:6.8,date:"2025-09-05"}],i={render:()=>e.jsxs(n,{children:[e.jsx(p,{children:"Recent papers with scores"}),e.jsx(m,{children:e.jsxs(c,{children:[e.jsx(r,{children:"Title"}),e.jsx(r,{children:"Source"}),e.jsx(r,{className:"text-right",children:"Score"}),e.jsx(r,{className:"text-right",children:"Date"})]})}),e.jsx(b,{children:x.map(a=>e.jsxs(c,{children:[e.jsx(d,{className:"font-medium",children:a.title}),e.jsx(d,{children:a.source}),e.jsx(d,{className:"text-right",children:a.score}),e.jsx(d,{className:"text-right",children:a.date})]},a.id))})]})};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  render: () => <Table>
      <TableCaption>Recent papers with scores</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Source</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead className="text-right">Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sampleData.map(paper => <TableRow key={paper.id}>
            <TableCell className="font-medium">{paper.title}</TableCell>
            <TableCell>{paper.source}</TableCell>
            <TableCell className="text-right">{paper.score}</TableCell>
            <TableCell className="text-right">{paper.date}</TableCell>
          </TableRow>)}
      </TableBody>
    </Table>
}`,...i.parameters?.docs?.source}}};const g=["Default"];export{i as Default,g as __namedExportsOrder,u as default};
