"use client";

import { useEffect, useState } from "react";

interface Alert {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: "info" | "warning" | "success" | "error";
}

export default function AlertFeed() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/alerts");
      if (!res.ok) throw new Error("Failed to fetch alerts");
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error(err);
      // Fallback data for preview purposes if backend is missing
      setAlerts([
        { id: "1", title: "Connection Error", message: "Could not reach backend API.", timestamp: new Date().toISOString(), type: "error" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const getTypeColor = (type: Alert["type"]) => {
    switch (type) {
      case "error": return "bg-red-500/20 text-red-400 border-red-500/30";
      case "warning": return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "success": return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      default: return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    }
  };

  return (
    <div className="glass-panel flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          System Alerts
        </h2>
        {isLoading && <div className="w-4 h-4 border-2 border-indigo-500/50 border-t-indigo-500 rounded-full animate-spin" />}
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {alerts.length === 0 && !isLoading ? (
          <div className="text-center text-slate-400 py-8 text-sm">
            No active alerts at this time.
          </div>
        ) : (
          alerts.map(alert => (
            <div key={alert.id} className={`p-3 rounded-xl border ${getTypeColor(alert.type)} backdrop-blur-sm`}>
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium text-sm text-slate-200">{alert.title}</span>
                <span className="text-xs opacity-60">
                  {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-sm opacity-80">{alert.message}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
