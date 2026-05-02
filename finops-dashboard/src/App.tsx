import { useState, useEffect } from 'react';

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
      <header className="fixed top-0 w-full z-50 bg-surface-dim/80 backdrop-blur-[20px] border-b border-outline-variant/10 shadow-[0_0_40px_rgba(161,250,255,0.05)]">
<div className="flex justify-between items-center h-16 px-8 max-w-[1920px] mx-auto font-['Inter'] antialiased">
<div className="flex items-center gap-4">
<span className="text-lg font-black tracking-widest text-[#a1faff] uppercase">SYNTHETIC LEDGER</span>
<span className="text-outline-variant px-2">|</span>
<span className="text-sm font-medium tracking-tight text-on-surface-variant">AVATAR INFRASTRUCTURE FINOPS</span>
</div>
<nav className="hidden md:flex items-center gap-8">
<a className="text-[#a1faff] border-b-2 border-[#00f4fe] pb-1 text-sm font-medium" href="#">Clusters</a>
<a className="text-[#a9abb0] hover:text-[#a1faff] transition-all duration-300 text-sm font-medium" href="#">Compute</a>
<a className="text-[#a9abb0] hover:text-[#a1faff] transition-all duration-300 text-sm font-medium" href="#">Storage</a>
<a className="text-[#a9abb0] hover:text-[#a1faff] transition-all duration-300 text-sm font-medium" href="#">Network</a>
</nav>
<div className="flex items-center gap-6">
<button className="material-symbols-outlined text-[#a9abb0] hover:text-[#a1faff] transition-colors">notifications_active</button>
<button className="material-symbols-outlined text-[#a9abb0] hover:text-[#a1faff] transition-colors">settings</button>
<div className="h-8 w-8 rounded-full bg-surface-container-high border border-outline-variant/20 overflow-hidden">
<img alt="Administrator Profile" className="w-full h-full object-cover" data-alt="Cybernetic 3D avatar of a system administrator with neon cyan accents and sleek matte black finish" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAENzQU_pj93Dt473tEawJRtL3oQDJdDFf2cRX8ct1qeSVOeCQp3P1ZJc09RtzbV62xfNF9qhDzwcijv8mHx1wVyAUWcG9rR6uoIG1ihwa_FbcLnT4IC7ZJXp_TVT6wLTNU0Wei1uh7_Y22BjQMJnPlc0ek85h4M3v-EGHjNiecmsJyBnUWep_V17kDjQaXDdbvAff4jyRyJ1JXPuyGhgATyj85q0PwO9hFDtfiW9mrX6PF9A-ecDo0xrWhjDvdQw6IHRLbLolsC5KD"/>
</div>
</div>
</div>
</header>
<aside className="h-screen w-64 fixed left-0 top-0 overflow-y-auto bg-surface-container-lowest pt-20 border-r border-outline-variant/10">
<div className="flex flex-col gap-2 p-4 font-['Inter'] font-light uppercase tracking-tight">
<div className="px-4 mb-6">
<h2 className="text-[#a1faff] font-bold text-xs tracking-widest">OPS_CORE</h2>
<p className="text-[10px] text-on-surface-variant">Active Nodes: 1,240</p>
</div>
<nav className="flex flex-col gap-1">
<a className="flex items-center gap-3 px-4 py-3 bg-surface-container-highest text-[#a1faff] border-r-4 border-[#00f4fe] transition-colors duration-200" href="#">
<span className="material-symbols-outlined text-[20px]">grid_view</span>
<span className="text-[11px] font-medium">Dashboard</span>
</a>
<a className="flex items-center gap-3 px-4 py-3 text-[#a9abb0] hover:bg-surface-container-high hover:text-white transition-colors duration-200" href="#">
<span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
<span className="text-[11px] font-medium">Asset Ledger</span>
</a>
<a className="flex items-center gap-3 px-4 py-3 text-[#a9abb0] hover:bg-surface-container-high hover:text-white transition-colors duration-200" href="#">
<span className="material-symbols-outlined text-[20px]">insights</span>
<span className="text-[11px] font-medium">Anomaly Pulse</span>
</a>
<a className="flex items-center gap-3 px-4 py-3 text-[#a9abb0] hover:bg-surface-container-high hover:text-white transition-colors duration-200" href="#">
<span className="material-symbols-outlined text-[20px]">dns</span>
<span className="text-[11px] font-medium">Infrastructure</span>
</a>
<a className="flex items-center gap-3 px-4 py-3 text-[#a9abb0] hover:bg-surface-container-high hover:text-white transition-colors duration-200" href="#">
<span className="material-symbols-outlined text-[20px]">terminal</span>
<span className="text-[11px] font-medium">Job Inspector</span>
</a>
</nav>
<div className="mt-8 px-4">
<button className="w-full py-2 bg-gradient-to-r from-primary to-primary-container text-on-primary-fixed font-bold text-[10px] rounded-md active:scale-[0.98] transition-transform">
                NEW DEPLOYMENT
            </button>
</div>
<div className="mt-auto pt-10 pb-4 border-t border-outline-variant/10">
<a className="flex items-center gap-3 px-4 py-2 text-[#a9abb0] hover:text-white transition-colors" href="#">
<span className="material-symbols-outlined text-[18px]">help_outline</span>
<span className="text-[10px]">Support</span>
</a>
<a className="flex items-center gap-3 px-4 py-2 text-[#a9abb0] hover:text-white transition-colors" href="#">
<span className="material-symbols-outlined text-[18px]">analytics</span>
<span className="text-[10px]">API Status</span>
</a>
</div>
</div>
</aside>
<main className="ml-64 pt-24 px-8 pb-12">

<div className="mb-10">
<h1 className="text-3xl font-extrabold tracking-tighter text-on-surface mb-2">Operational Spend</h1>
<div className="flex items-center gap-2">
<div className="w-2 h-2 rounded-full bg-primary relative">
<div className="absolute inset-0 bg-primary/40 rounded-full animate-ping"></div>
</div>
<span className="text-xs font-medium text-on-surface-variant tracking-wider uppercase">Live Ledger Sync: us-east-1a • us-west-2c</span>
</div>
</div>

<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
<div className="glass-panel p-6 rounded-xl border border-outline-variant/5">
<p className="text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-4">Total Spend (MTD)</p>
<div className="flex items-baseline gap-2">
<h3 className="text-3xl font-black text-on-surface tracking-tight">${finOps.totalSpend.toFixed(2)}</h3>
<span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded">+12%</span>
</div>
<div className="mt-4 h-1 w-full bg-surface-container rounded-full overflow-hidden">
<div className="h-full bg-primary w-3/4"></div>
</div>
</div>
<div className="glass-panel p-6 rounded-xl border border-outline-variant/5">
<p className="text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-4">Projected Bill</p>
<h3 className="text-3xl font-black text-on-surface tracking-tight">${finOps.projectedBill.toFixed(2)}</h3>
<p className="text-[10px] text-on-surface-variant mt-2 font-medium tracking-wide">ESTIMATED CYCLE END</p>
</div>
<div className="glass-panel p-6 rounded-xl border border-outline-variant/5">
<p className="text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-4">Active GPU Instances</p>
<div className="flex items-center gap-3">
<h3 className="text-3xl font-black text-on-surface tracking-tight">{finOps.activeGPUs}</h3>
<div className="px-2 py-1 bg-surface-container-high rounded-full border border-outline-variant/10">
<span className="text-[10px] font-bold text-secondary">L4/T4 MESH</span>
</div>
</div>
<p className="text-[10px] text-on-surface-variant mt-2 font-medium tracking-wide">100% RESOURCE ALLOCATION</p>
</div>
<div className="glass-panel p-6 rounded-xl border border-outline-variant/5">
<p className="text-xs font-medium text-on-surface-variant uppercase tracking-widest mb-4">Cost Efficiency</p>
<div className="flex items-center gap-4">
<h3 className="text-3xl font-black text-on-surface tracking-tight">{finOps.costEfficiency}%</h3>
<div className="flex-1 h-2 bg-surface-container-lowest rounded-full">
<div className="h-full bg-gradient-to-r from-primary to-secondary w-[94%] rounded-full shadow-[0_0_10px_rgba(161,250,255,0.4)]"></div>
</div>
</div>
<p className="text-[10px] text-on-surface-variant mt-2 font-medium tracking-wide">OPTIMIZED ARCHITECTURE</p>
</div>
</div>

<div className="glass-panel p-8 rounded-xl border border-outline-variant/5 mb-8">
<div className="flex justify-between items-center mb-10">
<div>
<h4 className="text-sm font-bold text-on-surface uppercase tracking-widest">Monthly Consumption Chart</h4>
<p className="text-[10px] text-on-surface-variant mt-1">Infrastructure cost trends across the previous two quarters</p>
</div>
<div className="flex gap-4 items-center">
<div className="flex items-center gap-2">
<div className="w-3 h-3 rounded-sm bg-primary shadow-[0_0_10px_rgba(0,244,254,0.3)]"></div>
<span className="text-[10px] font-bold text-on-surface-variant">LANA-ENGINE</span>
</div>
<div className="flex items-center gap-2">
<div className="w-3 h-3 rounded-sm bg-secondary"></div>
<span className="text-[10px] font-bold text-on-surface-variant">STREAMING-BRIDGE</span>
</div>
<select className="bg-surface-container-lowest border border-outline-variant/20 text-[10px] font-bold text-on-surface-variant rounded-md px-3 py-1.5 focus:ring-1 focus:ring-primary">
<option>H2 2023 - H1 2024</option>
</select>
</div>
</div>
<div className="h-56 relative flex items-end gap-1 px-4">

<div className="absolute left-0 bottom-0 top-0 w-px bg-outline-variant/10"></div>
<div className="absolute left-0 bottom-0 right-0 h-px bg-outline-variant/10"></div>

<div className="absolute left-0 right-0 top-1/4 h-px bg-outline-variant/5 border-t border-dashed border-outline-variant/10"></div>
<div className="absolute left-0 right-0 top-2/4 h-px bg-outline-variant/5 border-t border-dashed border-outline-variant/10"></div>
<div className="absolute left-0 right-0 top-3/4 h-px bg-outline-variant/5 border-t border-dashed border-outline-variant/10"></div>

<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t-sm h-[35%]"></div>
<div className="w-1/3 bg-secondary/20 hover:bg-secondary transition-all duration-300 rounded-t-sm h-[20%]"></div>
<span className="text-[9px] mt-4 text-on-surface-variant font-bold tracking-tighter absolute -bottom-6">OCT</span>
</div>
<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t-sm h-[45%]"></div>
<div className="w-1/3 bg-secondary/20 hover:bg-secondary transition-all duration-300 rounded-t-sm h-[25%]"></div>
<span className="text-[9px] mt-4 text-on-surface-variant font-bold tracking-tighter absolute -bottom-6">NOV</span>
</div>
<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t-sm h-[40%]"></div>
<div className="w-1/3 bg-secondary/20 hover:bg-secondary transition-all duration-300 rounded-t-sm h-[30%]"></div>
<span className="text-[9px] mt-4 text-on-surface-variant font-bold tracking-tighter absolute -bottom-6">DEC</span>
</div>
<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t-sm h-[65%]"></div>
<div className="w-1/3 bg-secondary/20 hover:bg-secondary transition-all duration-300 rounded-t-sm h-[40%]"></div>
<span className="text-[9px] mt-4 text-on-surface-variant font-bold tracking-tighter absolute -bottom-6">JAN</span>
</div>
<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary/20 hover:bg-primary transition-all duration-300 rounded-t-sm h-[80%]"></div>
<div className="w-1/3 bg-secondary/20 hover:bg-secondary transition-all duration-300 rounded-t-sm h-[55%]"></div>
<span className="text-[9px] mt-4 text-on-surface-variant font-bold tracking-tighter absolute -bottom-6">FEB</span>
</div>
<div className="flex-1 flex flex-col items-center group relative h-full justify-end">
<div className="w-1/3 bg-primary shadow-[0_0_15px_rgba(0,244,254,0.4)] rounded-t-sm h-[95%]"></div>
<div className="w-1/3 bg-secondary shadow-[0_0_10px_rgba(146,155,250,0.4)] rounded-t-sm h-[60%]"></div>
<span className="text-[9px] mt-4 text-primary font-bold tracking-tighter absolute -bottom-6">MAR</span>
</div>
</div>
</div>

<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

<div className="lg:col-span-2 glass-panel rounded-xl border border-outline-variant/5 flex flex-col h-full overflow-hidden">
<div className="p-6 border-b border-outline-variant/10 flex justify-between items-center">
<div className="flex items-center gap-3">
<span className="material-symbols-outlined text-primary text-xl">biotech</span>
<h4 className="text-sm font-bold text-on-surface uppercase tracking-widest">Avatar Job Inspector <span className="text-primary-dim ml-2 font-medium opacity-60">(LIVE)</span></h4>
</div>
<div className="text-[10px] font-mono text-primary bg-primary/5 px-2 py-1 rounded border border-primary/20">
                    ID: JOB-8812-US-WEST-2
                </div>
</div>
<div className="p-8 flex flex-col flex-1">

<div className="flex justify-between items-start mb-10 relative">

<div className="absolute top-4 left-0 right-0 h-0.5 bg-outline-variant/20 -z-10"></div>
<div className="absolute top-4 left-0 w-2/3 h-0.5 bg-primary -z-10"></div>

<div className="flex flex-col items-center gap-3 group">
<div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary text-xs font-bold ring-4 ring-surface-dim">1</div>
<span className="text-[10px] font-bold text-on-surface-variant group-hover:text-primary transition-colors">Provisioning L4 GPU</span>
</div>
<div className="flex flex-col items-center gap-3 group">
<div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary text-xs font-bold ring-4 ring-surface-dim">2</div>
<span className="text-[10px] font-bold text-on-surface-variant group-hover:text-primary transition-colors">Extracting Audio</span>
</div>
<div className="flex flex-col items-center gap-3 group">
<div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary text-xs font-bold ring-4 ring-primary/30 animate-glow-pulse">3</div>
<span className="text-[10px] font-bold text-primary tracking-wide">LatentSync Inference (ACTIVE)</span>
</div>
<div className="flex flex-col items-center gap-3 group">
<div className="w-8 h-8 rounded-full bg-surface-container-high border-2 border-outline-variant/40 flex items-center justify-center text-on-surface-variant text-xs font-bold ring-4 ring-surface-dim">4</div>
<span className="text-[10px] font-bold text-on-surface-variant opacity-40">Uploading to GCS</span>
</div>
</div>

<div className="flex-1 bg-[#090b0d] border border-outline-variant/20 rounded-lg p-4 font-mono text-[11px] overflow-hidden flex flex-col">
<div className="flex items-center gap-2 mb-3 border-b border-outline-variant/10 pb-2">
<div className="flex gap-1.5">
<div className="w-2.5 h-2.5 rounded-full bg-error/40"></div>
<div className="w-2.5 h-2.5 rounded-full bg-warning/40"></div>
<div className="w-2.5 h-2.5 rounded-full bg-success/40"></div>
</div>
<span className="text-[10px] text-on-surface-variant ml-2 opacity-50 uppercase tracking-tighter">Terminal — lana-engine-04</span>
</div>
<div className="terminal-scroll overflow-y-auto space-y-1.5 flex-1 max-h-[160px]">
<p className="text-on-surface-variant"><span className="text-primary-dim opacity-60 mr-2">[09:41:22]</span> Initializing CUDA context on device: 0 (Tesla L4)</p>
<p className="text-on-surface-variant"><span className="text-primary-dim opacity-60 mr-2">[09:41:23]</span> Successfully allocated 16.2GB VRAM</p>
<p className="text-on-surface-variant"><span className="text-primary-dim opacity-60 mr-2">[09:41:24]</span> Loading LatentSync weights v2.1.0...</p>
<p className="text-on-surface-variant"><span className="text-primary-dim opacity-60 mr-2">[09:41:27]</span> Checkpoint loaded. Latency: 42ms</p>
<p className="text-primary"><span className="text-primary-dim opacity-60 mr-2">[09:41:28]</span> Processing frame 234/1200... <span className="ml-4 opacity-70">[||||||||||||||||-----------] 62.4 FPS</span></p>
<p className="text-on-surface-variant"><span className="text-primary-dim opacity-60 mr-2">[09:41:29]</span> Synchronizing audio buffer with visual sync map...</p>
<p className="text-primary animate-pulse"><span className="text-primary-dim opacity-60 mr-2">[09:41:30]</span> Processing frame 289/1200... <span className="ml-4 opacity-70">[|||||||||||||||||----------] 61.8 FPS</span></p>
</div>
</div>
</div>
</div>

<div className="flex flex-col gap-6">
<div className="glass-panel p-6 rounded-xl border border-outline-variant/5">
<h4 className="text-sm font-bold text-on-surface uppercase tracking-widest mb-6">Actionable Insights</h4>
<div className="space-y-4">
<div className="p-4 bg-tertiary/10 rounded-lg border-l-4 border-tertiary">
<div className="flex items-start gap-3">
<span className="material-symbols-outlined text-tertiary">warning</span>
<div>
<p className="text-[11px] font-bold text-on-surface">3 idle T4 instances detected</p>
<p className="text-[10px] text-on-surface-variant mt-1">Resource under-utilization identified in Cluster-X4.</p>
<button className="mt-3 text-[10px] font-black text-tertiary hover:underline uppercase">Decommission Now</button>
</div>
</div>
</div>
<div className="p-4 bg-primary/10 rounded-lg border-l-4 border-primary">
<div className="flex items-start gap-3">
<span className="material-symbols-outlined text-primary">auto_fix_high</span>
<div>
<p className="text-[11px] font-bold text-on-surface">Storage optimization available</p>
<p className="text-[10px] text-on-surface-variant mt-1">Migration to Archive Tier can save $45/mo.</p>
<button className="mt-3 text-[10px] font-black text-primary hover:underline uppercase">Automate Policy</button>
</div>
</div>
</div>
</div>
</div>
<div className="flex-1 glass-panel rounded-xl border border-outline-variant/5 overflow-hidden relative group min-h-[160px]">
<img alt="Infrastructure Heatmap" className="w-full h-full object-cover opacity-30 group-hover:scale-110 transition-transform duration-[3s]" src="https://lh3.googleusercontent.com/aida-public/AB6AXuB-2fJ3n9W5HuQEp8_XH14thREALrV9M-5WLNlszZijkzOVdsuwgKn1TKQ80lK72UubD5aTtc0OmNbHuFBUP9uR2_5zeOzq2g0zmChC-b-CcJGM9N9EUaPtYjIUmk-lodQLnJBfTS83VTPvycl6xFwkdClz_UFCxlF1XG_CdtAB_IVU62q8jg9AGZaKSDv304OlqglKY25T8-9PR25VUU0VHnAsJVVRC21h_-_jq-RtjJ9S6ixlzexRquDXg80JQC_u1tZ1ZaaVz1NH"/>
<div className="absolute inset-0 bg-gradient-to-t from-surface-dim to-transparent p-6 flex flex-col justify-end">
<h5 className="text-xs font-black text-primary tracking-widest mb-1 uppercase">Infrastructure Health</h5>
<div className="flex items-center gap-2">
<div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
<p className="text-[10px] text-on-surface-variant">Last security audit completed 2h ago. All systems operational.</p>
</div>
</div>
</div>
</div>
</div>
</main>

    </div>
  );
}
