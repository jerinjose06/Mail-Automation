"use client";

import { useEffect, useState } from "react";

interface Rule {
  id: string;
  name: string;
  condition: string;
  action: string;
  active: boolean;
}

export default function RulesManager() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Form state
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCondition, setNewCondition] = useState("");
  const [newAction, setNewAction] = useState("");

  const fetchRules = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/rules");
      if (!res.ok) throw new Error("Failed to fetch rules");
      const data = await res.json();
      setRules(data.rules || []);
    } catch (err) {
      console.error(err);
      // Fallback
      setRules([
        { id: "1", name: "Spam Filter", condition: "subject contains 'viagra'", action: "move to junk", active: true },
        { id: "2", name: "VIP Auto-reply", condition: "sender is 'boss@company.com'", action: "auto-reply 'Got it'", active: false }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newCondition || !newAction) return;
    
    setIsLoading(true);
    try {
      const newRule = { name: newName, condition: newCondition, action: newAction, active: true };
      const res = await fetch("http://localhost:8000/api/rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newRule),
      });
      
      if (res.ok) {
        setIsAdding(false);
        setNewName("");
        setNewCondition("");
        setNewAction("");
        fetchRules();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRule = async (id: string, currentStatus: boolean) => {
    // In a real app we would send a PATCH to /api/rules/:id
    setRules(rules.map(r => r.id === id ? { ...r, active: !currentStatus } : r));
  };

  return (
    <div className="glass-panel flex flex-col h-full">
      <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Automation Rules
        </h2>
        <button 
          onClick={() => setIsAdding(!isAdding)}
          className="text-sm bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 px-3 py-1.5 rounded-lg transition-colors border border-indigo-500/30"
        >
          {isAdding ? "Cancel" : "+ New Rule"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isAdding && (
          <form onSubmit={handleAddRule} className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10 space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Rule Name</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} className="glass-input w-full py-2 text-sm" placeholder="e.g. Invoice Forwarding" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Condition</label>
              <input value={newCondition} onChange={e => setNewCondition(e.target.value)} className="glass-input w-full py-2 text-sm" placeholder="e.g. subject contains 'invoice'" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Action</label>
              <input value={newAction} onChange={e => setNewAction(e.target.value)} className="glass-input w-full py-2 text-sm" placeholder="e.g. forward to accounting@company.com" />
            </div>
            <div className="pt-2">
              <button type="submit" disabled={isLoading} className="glass-button w-full py-2 text-sm">Save Rule</button>
            </div>
          </form>
        )}

        <div className="space-y-3">
          {rules.length === 0 && !isLoading ? (
            <div className="text-center text-slate-400 py-8 text-sm">No rules configured.</div>
          ) : (
            rules.map(rule => (
              <div key={rule.id} className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors group">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-slate-200">{rule.name}</h3>
                    <div className="mt-2 space-y-1 text-xs font-mono text-slate-400">
                      <div className="flex gap-2">
                        <span className="text-indigo-400 w-6">IF</span>
                        <span className="bg-black/20 px-1.5 py-0.5 rounded text-slate-300">{rule.condition}</span>
                      </div>
                      <div className="flex gap-2">
                        <span className="text-emerald-400 w-6">THEN</span>
                        <span className="bg-black/20 px-1.5 py-0.5 rounded text-slate-300">{rule.action}</span>
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => toggleRule(rule.id, rule.active)}
                    className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${rule.active ? 'bg-indigo-500' : 'bg-slate-700'}`}
                  >
                    <span className="sr-only">Toggle rule</span>
                    <span aria-hidden="true" className={`pointer-events-none absolute left-0 inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition-transform duration-200 ease-in-out ${rule.active ? 'translate-x-4' : 'translate-x-0'}`} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
