const fs = require('fs');

let html = fs.readFileSync('../dashboard_final.html', 'utf8');

let bodyMatch = html.match(/<main[\s\S]*?<\/main>/i);
let headerMatch = html.match(/<header[\s\S]*?<\/header>/i);
let asideMatch = html.match(/<aside[\s\S]*?<\/aside>/i);

let body = "";
if (headerMatch) body += headerMatch[0] + "\n";
if (asideMatch) body += asideMatch[0] + "\n";
if (bodyMatch) body += bodyMatch[0] + "\n";

// Convert class to className
body = body.replace(/class=/g, 'className=');
body = body.replace(/<!--[\s\S]*?-->/g, '');

// Self closing tags fix
body = body.replace(/<img([^>]+?)(?<!\/)>/g, '<img$1/>');
body = body.replace(/<input([^>]+?)(?<!\/)>/g, '<input$1/>');

// Hardcoded values to dynamic
body = body.replace(/\$4,250\.30|\$1\.15/, '${finOps.totalSpend.toFixed(2)}');
body = body.replace(/\$5,100\.00|\$2\.50/, '${finOps.projectedBill.toFixed(2)}');
body = body.replace(/<h3 className="text-3xl font-black text-on-surface tracking-tight">8<\/h3>|<h3 className="text-3xl font-black text-on-surface tracking-tight">0<\/h3>/, '<h3 className="text-3xl font-black text-on-surface tracking-tight">{finOps.activeGPUs}</h3>');
body = body.replace(/94%/, '{finOps.costEfficiency}%');

const code = `import { useState, useEffect } from 'react';

export default function App() {
  const [finOps, setFinOps] = useState({
    totalSpend: 1.15,
    projectedBill: 2.50,
    activeGPUs: 0,
    costEfficiency: 98
  });

  const [logs, setLogs] = useState([
    "[09:41:22] Initializing CUDA context on device: 0 (Tesla L4)",
    "[09:41:23] Successfully allocated 16.2GB VRAM",
    "[09:41:24] Waiting for Avatar Job request..."
  ]);

  return (
    <div className="bg-surface-dim text-on-surface min-h-screen">
      ${body}
    </div>
  );
}
`;

fs.writeFileSync('./src/App.tsx', code);
console.log("Converted successfully!");
