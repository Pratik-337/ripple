import React, { useState } from "react";
import { ArrowLeft, GitBranch, Search, Filter, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { cn } from "@/src/lib/utils";
import { Particles } from "./ui/particles";

type ChangeStatus = "needs_action" | "submitted" | "resolved";

interface GlobalChange {
    id: string;
    title: string;
    project: string;
    component: string;
    author: string;
    status: ChangeStatus;
    time: string;
    impactDetails?: string;
    acknowledgedCount?: number;
    totalRequired?: number;
}

const MOCK_CHANGES: GlobalChange[] = [
    {
        id: "c1",
        title: "validateUser signature update",
        project: "Auth Service",
        component: "Dashboard",
        author: "Raj Patel",
        status: "needs_action",
        time: "1 hour ago",
        impactDetails: "Your Dashboard component is affected · 2 lines",
    },
    {
        id: "c2",
        title: "Checkout flow refactor",
        project: "Payments API",
        component: "API Gateway",
        author: "Sarah Chen",
        status: "needs_action",
        time: "3 hours ago",
        impactDetails: "Your API Gateway component is affected · 4 lines",
    },
    {
        id: "c3",
        title: "Updated user types",
        project: "Auth Service",
        component: "Core Models",
        author: "Alex Rivera",
        status: "submitted",
        time: "2 hours ago",
        acknowledgedCount: 2,
        totalRequired: 3,
    },
    {
        id: "c4",
        title: "Fixed token refresh logic",
        project: "Auth Service",
        component: "JWT Handler",
        author: "Priya Sharma",
        status: "resolved",
        time: "1 day ago",
    },
    {
        id: "c5",
        title: "Removed deprecated endpoints",
        project: "Payments API",
        component: "Legacy Routes",
        author: "Raj Patel",
        status: "resolved",
        time: "2 days ago",
    },
];

export const GlobalChangesPage = ({ onBack }: { onBack: () => void }) => {
    const [filter, setFilter] = useState<"all" | "needs_action" | "submitted">("all");
    const [query, setQuery] = useState("");

    const filteredChanges = MOCK_CHANGES.filter(c => {
        const matchesSearch = c.title.toLowerCase().includes(query.toLowerCase()) ||
            c.project.toLowerCase().includes(query.toLowerCase());

        if (filter === "needs_action") return matchesSearch && c.status === "needs_action";
        if (filter === "submitted") return matchesSearch && c.status === "submitted";
        return matchesSearch;
    });

    const needsAction = filteredChanges.filter(c => c.status === "needs_action");
    const submitted = filteredChanges.filter(c => c.status === "submitted");
    const resolved = filteredChanges.filter(c => c.status === "resolved");

    return (
        <div className="flex h-screen bg-black text-white overflow-hidden relative">
            <div className="fixed inset-0 z-0 pointer-events-none">
                <Particles quantity={120} className="absolute inset-0 h-full w-full" color="#ffffff" staticity={80} size={0.3} />
            </div>

            <main className="relative z-10 flex-1 flex flex-col min-w-0 h-full">
                {/* Header */}
                <header className="h-16 border-b border-white/[0.06] flex items-center justify-between px-6 bg-black/40 backdrop-blur-sm shrink-0">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onBack}
                            className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-lg bg-white/10 flex items-center justify-center border border-white/10">
                                <GitBranch className="h-4 w-4 text-white" />
                            </div>
                            <h1 className="text-lg font-bold">My Changes</h1>
                        </div>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 md:p-10">
                    <div className="max-w-4xl mx-auto">
                        {/* Top Bar */}
                        <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
                            <div className="relative w-full md:w-96">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/20" />
                                <input
                                    type="text"
                                    value={query}
                                    onChange={e => setQuery(e.target.value)}
                                    placeholder="Search changes..."
                                    className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/20 transition-colors"
                                />
                            </div>

                            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto scrollbar-hide">
                                <Filter className="h-4 w-4 text-white/30 mr-1 shrink-0" />
                                {[
                                    { id: "all", label: "All" },
                                    { id: "needs_action", label: "Needs my action" },
                                    { id: "submitted", label: "Submitted by me" },
                                ].map(f => (
                                    <button
                                        key={f.id}
                                        onClick={() => setFilter(f.id as any)}
                                        className={cn(
                                            "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
                                            filter === f.id
                                                ? "bg-white text-black"
                                                : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
                                        )}
                                    >
                                        {f.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-10">
                            {/* Needs Action Section */}
                            {(filter === "all" || filter === "needs_action") && needsAction.length > 0 && (
                                <section>
                                    <h2 className="text-xs font-bold tracking-wider text-orange-400 uppercase mb-4 flex items-center gap-2">
                                        <AlertCircle className="h-4 w-4" />
                                        Needs Your Action ({needsAction.length})
                                    </h2>
                                    <div className="space-y-3">
                                        {needsAction.map(c => (
                                            <div key={c.id} className="group bg-white/[0.03] border border-orange-500/20 hover:border-orange-500/40 rounded-2xl p-5 transition-all duration-300">
                                                <div className="flex items-start justify-between mb-2">
                                                    <div className="flex items-start gap-4">
                                                        <div className="mt-0.5 h-3 w-3 rounded-full bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)] shrink-0" />
                                                        <div>
                                                            <h3 className="text-base font-semibold text-white group-hover:text-orange-100 transition-colors">
                                                                {c.title}
                                                            </h3>
                                                            <div className="flex items-center gap-2 mt-1 text-xs">
                                                                <span className="text-white/40">{c.project}</span>
                                                                <div className="h-1 w-1 rounded-full bg-white/10" />
                                                                <span className="text-white/30">Submitted by {c.author}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <span className="text-xs text-white/30 shrink-0 whitespace-nowrap">{c.time}</span>
                                                </div>
                                                <div className="flex items-center justify-between mt-4 pl-7">
                                                    <span className="text-sm text-orange-400/80 font-medium">
                                                        {c.impactDetails}
                                                    </span>
                                                    <button className="flex items-center gap-1.5 text-xs font-medium text-orange-400 hover:text-orange-300 bg-orange-400/10 hover:bg-orange-400/20 px-3 py-1.5 rounded-lg transition-colors">
                                                        Review Impact &rarr;
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Submitted Section */}
                            {(filter === "all" || filter === "submitted") && submitted.length > 0 && (
                                <section>
                                    <h2 className="text-xs font-bold tracking-wider text-white/40 uppercase mb-4 flex items-center gap-2">
                                        <Clock className="h-4 w-4" />
                                        Submitted by You ({submitted.length})
                                    </h2>
                                    <div className="space-y-3">
                                        {submitted.map(c => (
                                            <div key={c.id} className="group bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] rounded-2xl p-5 transition-all duration-300">
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-4 w-4 rounded-full border border-white/30 flex items-center justify-center">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-transparent" />
                                                        </div>
                                                        <h3 className="text-[15px] font-semibold text-white">{c.title}</h3>
                                                    </div>
                                                    <span className="text-xs text-white/30">{c.time}</span>
                                                </div>
                                                <div className="flex items-center justify-between pl-7">
                                                    <div className="flex items-center gap-3 text-xs">
                                                        <span className="text-white/40 font-medium">{c.project}</span>
                                                        <div className="h-1 w-1 rounded-full bg-white/10" />
                                                        <span className="text-white/60">
                                                            {c.acknowledgedCount} of {c.totalRequired} acknowledged
                                                        </span>
                                                    </div>
                                                    <button className="text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors">
                                                        View Review &rarr;
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Resolved Section */}
                            {filter === "all" && resolved.length > 0 && (
                                <section>
                                    <h2 className="text-xs font-bold tracking-wider text-white/30 uppercase mb-4 flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4" />
                                        Recently Resolved ({resolved.length})
                                    </h2>
                                    <div className="space-y-3 opacity-60 hover:opacity-100 transition-opacity duration-300">
                                        {resolved.map(c => (
                                            <div key={c.id} className="flex items-center justify-between bg-white/[0.01] border border-white/[0.04] rounded-xl p-4">
                                                <div className="flex items-center gap-3">
                                                    <CheckCircle2 className="h-4 w-4 text-emerald-500/50" />
                                                    <div>
                                                        <p className="text-sm font-medium text-white/80">{c.title}</p>
                                                        <p className="text-[11px] text-white/30 mt-0.5">{c.project} · Approved {c.time}</p>
                                                    </div>
                                                </div>
                                                <button className="text-xs text-white/40 hover:text-white transition-colors">
                                                    View
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {filteredChanges.length === 0 && (
                                <div className="text-center py-20 border border-white/5 rounded-2xl bg-white/[0.02]">
                                    <GitBranch className="h-8 w-8 text-white/10 mx-auto mb-3" />
                                    <p className="text-white/40">No changes match your criteria.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};
