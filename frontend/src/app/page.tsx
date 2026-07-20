import ChatInterface from "@/components/ChatInterface";
import AlertFeed from "@/components/AlertFeed";
import RulesManager from "@/components/RulesManager";

export default function Home() {
  return (
    <main className="min-h-screen p-4 md:p-8 flex flex-col max-w-7xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
            Local Email Agent
          </h1>
          <p className="text-slate-400 mt-1">Autonomous inbox management & intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            Backend Connected
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)] min-h-[700px]">
        {/* Left Column: Chat */}
        <div className="lg:col-span-7 flex flex-col h-full">
          <ChatInterface />
        </div>

        {/* Right Column: Rules and Alerts */}
        <div className="lg:col-span-5 flex flex-col gap-6 h-full">
          <div className="flex-1 min-h-0">
            <RulesManager />
          </div>
          <div className="h-64 shrink-0">
            <AlertFeed />
          </div>
        </div>
      </div>
    </main>
  );
}
