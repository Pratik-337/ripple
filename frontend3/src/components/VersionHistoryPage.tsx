import React, { useState, useRef } from "react";
import { DiffEditor } from "@monaco-editor/react";
import {
    ArrowLeft, Waves, GitMerge, ChevronDown, ChevronUp,
    Clock, FileCode2, Users, RotateCcw, Filter, Search,
    CheckCircle2, X, Loader2, Network, Shield, Eye, Lock,
    ChevronRight, History, Zap
} from "lucide-react";
import { cn } from "@/src/lib/utils";
import { Particles } from "@/src/components/ui/particles";

// ─── Types ───────────────────────────────────────────────────────────────────

interface HistoryEntry {
    id: string;
    title: string;
    description?: string;
    author: { name: string; initials: string; color: string };
    component: string;
    affectedComponents: string[];
    mergedAt: string;
    mergedAtRelative: string;
    filesChanged: number;
    acknowledgedCount: number;
    totalAcknowledged: number;
    strictnessMode: "visibility" | "soft" | "full";
    diff: { original: string; modified: string; filename: string };
    isRestore?: boolean;
}

// ─── Mock History Data ────────────────────────────────────────────────────────

const MOCK_HISTORY: HistoryEntry[] = [
    {
        id: "h1",
        title: "Updated validateUser signature",
        description: "Added optional `options` parameter for role-gated validation and strict JWT mode.",
        author: { name: "Priya Sharma", initials: "PS", color: "from-emerald-500 to-green-600" },
        component: "Authentication",
        affectedComponents: ["Dashboard UI", "Checkout & Payment"],
        mergedAt: "Feb 23, 2026 · 00:12",
        mergedAtRelative: "28 min ago",
        filesChanged: 2,
        acknowledgedCount: 2,
        totalAcknowledged: 2,
        strictnessMode: "soft",
        diff: {
            filename: "src/auth/auth.ts",
            original: `export async function validateUser(\n  user: User,\n  token: string\n): Promise<boolean> {\n  const decoded = verifyJWT(token);\n  return decoded?.userId === user.id;\n}`,
            modified: `export async function validateUser(\n  user: User,\n  token: string,\n  options: Options = {}\n): Promise<boolean> {\n  const decoded = verifyJWT(token, options.strict);\n  if (options.requiredRole && user.role !== options.requiredRole) return false;\n  return decoded?.userId === user.id;\n}`,
        },
    },
    {
        id: "h2",
        title: "Refactored API route handlers",
        author: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
        component: "API Gateway",
        affectedComponents: ["Notification Service"],
        mergedAt: "Feb 22, 2026 · 18:44",
        mergedAtRelative: "5 hours ago",
        filesChanged: 3,
        acknowledgedCount: 1,
        totalAcknowledged: 1,
        strictnessMode: "soft",
        diff: {
            filename: "src/gateway/routes.ts",
            original: `router.get("/users", handler)\nrouter.post("/users", handler)\nrouter.delete("/users/:id", handler)`,
            modified: `router.get("/users", authenticate, handler)\nrouter.post("/users", authenticate, validate, handler)\nrouter.delete("/users/:id", authenticate, authorize("admin"), handler)`,
        },
    },
    {
        id: "h3",
        title: "Added order confirmation event",
        description: "Checkout now emits `order.confirmed` after successful payment.",
        author: { name: "Mia Wong", initials: "MW", color: "from-cyan-500 to-teal-600" },
        component: "Checkout & Payment",
        affectedComponents: ["Notification Service"],
        mergedAt: "Feb 22, 2026 · 14:21",
        mergedAtRelative: "Yesterday",
        filesChanged: 1,
        acknowledgedCount: 1,
        totalAcknowledged: 1,
        strictnessMode: "visibility",
        diff: {
            filename: "src/checkout/confirm.ts",
            original: `await processPayment(order);\nreturn { success: true };`,
            modified: `await processPayment(order);\nemit("order.confirmed", { orderId: order.id, userId: order.userId });\nreturn { success: true };`,
        },
    },
    {
        id: "h4",
        title: "Optimised search index rebuild",
        author: { name: "Raj Patel", initials: "RP", color: "from-amber-500 to-orange-600" },
        component: "Search & Indexing",
        affectedComponents: [],
        mergedAt: "Feb 21, 2026 · 09:05",
        mergedAtRelative: "2 days ago",
        filesChanged: 4,
        acknowledgedCount: 0,
        totalAcknowledged: 0,
        strictnessMode: "visibility",
        diff: {
            filename: "src/search/indexer.ts",
            original: `for (const doc of docs) {\n  await index.add(doc);\n}`,
            modified: `await index.addBatch(docs, { concurrency: 4 });\nawait index.flush();`,
        },
    },
    {
        id: "h5",
        title: "Bootstrapped notification templates",
        author: { name: "Sarah Chen", initials: "SC", color: "from-rose-500 to-pink-600" },
        component: "Notification Service",
        affectedComponents: [],
        mergedAt: "Feb 20, 2026 · 22:30",
        mergedAtRelative: "3 days ago",
        filesChanged: 6,
        acknowledgedCount: 0,
        totalAcknowledged: 0,
        strictnessMode: "full",
        diff: {
            filename: "src/notifications/templates.ts",
            original: `// no templates yet`,
            modified: `export const TEMPLATES = {\n  invite: (name: string) => \`You've been invited by \${name}\`,\n  changeReview: (comp: string) => \`\${comp} needs your review\`,\n  merged: (title: string) => \`Change merged: \${title}\`,\n};`,
        },
    },
    {
        id: "h6",
        title: "Restored to v3 snapshot",
        author: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
        component: "Authentication",
        affectedComponents: [],
        mergedAt: "Feb 19, 2026 · 11:12",
        mergedAtRelative: "4 days ago",
        filesChanged: 2,
        acknowledgedCount: 0,
        totalAcknowledged: 0,
        strictnessMode: "soft",
        isRestore: true,
        diff: {
            filename: "src/auth/auth.ts",
            original: `// after\nexport async function validateUser(user: User, token: string) {}`,
            modified: `// restored to stable\nexport async function validateUser(user: User, token: string) {}`,
        },
    },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

const Avatar = ({ initials, color, size = "sm" }: { initials: string; color: string; size?: "xs" | "sm" }) => {
    const sz = { xs: "h-5 w-5 text-[9px]", sm: "h-7 w-7 text-[10px]" }[size];
    return (
        <div className={cn("rounded-full bg-gradient-to-br flex items-center justify-center font-bold text-white shrink-0", sz, color)}>
            {initials}
        </div>
    );
};

const StrictnessBadge = ({ mode }: { mode: "visibility" | "soft" | "full" }) => {
    const cfg = {
        visibility: { label: "Visibility", icon: Eye, cls: "text-white/40 bg-white/5 border-white/10" },
        soft: { label: "Soft", icon: Shield, cls: "text-amber-400 bg-amber-400/10 border-amber-400/20" },
        full: { label: "Full", icon: Lock, cls: "text-violet-400 bg-violet-400/10 border-violet-400/20" },
    }[mode];
    const Icon = cfg.icon;
    return (
        <span className={cn("inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full border", cfg.cls)}>
            <Icon className="h-2.5 w-2.5" />{cfg.label}
        </span>
    );
};

// ─── Restore Confirmation Modal ───────────────────────────────────────────────

const RestoreModal = ({
    entry,
    onConfirm,
    onCancel,
}: {
    entry: HistoryEntry;
    onConfirm: () => void;
    onCancel: () => void;
}) => {
    const [loading, setLoading] = useState(false);

    const handleConfirm = () => {
        setLoading(true);
        setTimeout(() => { setLoading(false); onConfirm(); }, 1500);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
            <div className="relative bg-zinc-950 border border-white/10 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
                <div className="flex items-center gap-3 mb-4">
                    <div className="h-9 w-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
                        <RotateCcw className="h-4 w-4 text-amber-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-white">Restore this version?</h3>
                        <p className="text-[11px] text-white/35 mt-0.5">{entry.mergedAt}</p>
                    </div>
                </div>

                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3 mb-5">
                    <p className="text-xs font-medium text-white mb-0.5">{entry.title}</p>
                    <p className="text-[11px] text-white/40">{entry.component}</p>
                </div>

                <p className="text-xs text-white/40 leading-relaxed mb-5">
                    This will create a new change entry reverting <span className="text-white/70">{entry.component}</span> to the state it was in at this point. All affected contributors will be looped in automatically.
                </p>

                <div className="flex gap-2">
                    <button
                        onClick={onCancel}
                        className="flex-1 py-2.5 text-xs font-medium text-white/40 hover:text-white border border-white/10 hover:border-white/20 rounded-xl transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        id="confirm-restore-btn"
                        onClick={handleConfirm}
                        disabled={loading}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-white text-black text-xs font-bold rounded-xl hover:bg-white/90 transition-colors disabled:opacity-60"
                    >
                        {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="h-3.5 w-3.5" />}
                        {loading ? "Restoring..." : "Restore"}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ─── History Entry Card ───────────────────────────────────────────────────────

const HistoryCard = ({
    entry,
    isFirst,
    isLast,
    onRestore,
}: {
    entry: HistoryEntry;
    isFirst: boolean;
    isLast: boolean;
    onRestore: (entry: HistoryEntry) => void;
}) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="relative flex gap-4">
            {/* Timeline spine */}
            <div className="flex flex-col items-center shrink-0 w-8">
                <div className={cn(
                    "h-8 w-0.5 shrink-0",
                    isFirst ? "bg-transparent" : "bg-white/[0.06]"
                )} />
                <div className={cn(
                    "h-7 w-7 rounded-full border flex items-center justify-center shrink-0 z-10",
                    entry.isRestore
                        ? "bg-amber-500/10 border-amber-500/30"
                        : "bg-zinc-900 border-white/[0.10]"
                )}>
                    {entry.isRestore
                        ? <RotateCcw className="h-3 w-3 text-amber-400" />
                        : <GitMerge className="h-3 w-3 text-emerald-400" />
                    }
                </div>
                {!isLast && <div className="flex-1 w-0.5 bg-white/[0.06] mt-0" />}
            </div>

            {/* Card */}
            <div className={cn(
                "flex-1 mb-3 border rounded-2xl overflow-hidden transition-all duration-200",
                entry.isRestore
                    ? "bg-amber-500/[0.03] border-amber-500/15"
                    : "bg-white/[0.02] hover:bg-white/[0.04] border-white/[0.06] hover:border-white/[0.10]"
            )}>
                {/* Card header */}
                <div className="px-5 py-4">
                    <div className="flex items-start gap-3">
                        <Avatar initials={entry.author.initials} color={entry.author.color} size="sm" />
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                {entry.isRestore && (
                                    <span className="text-[10px] font-semibold text-amber-400/80 bg-amber-400/10 border border-amber-400/15 px-1.5 py-0.5 rounded-full">
                                        Restored
                                    </span>
                                )}
                                <p className="text-[13px] font-semibold text-white leading-snug">{entry.title}</p>
                            </div>
                            {entry.description && (
                                <p className="text-[11px] text-white/35 leading-relaxed mb-2">{entry.description}</p>
                            )}

                            {/* Meta row */}
                            <div className="flex items-center gap-3 flex-wrap text-[11px] text-white/30">
                                <span className="font-medium text-white/50">{entry.author.name}</span>
                                <span className="text-white/15">·</span>
                                <span>{entry.component}</span>
                                <span className="text-white/15">·</span>
                                <span className="flex items-center gap-1"><Clock className="h-2.5 w-2.5" />{entry.mergedAtRelative}</span>
                                <span className="text-white/15">·</span>
                                <span className="flex items-center gap-1"><FileCode2 className="h-2.5 w-2.5" />{entry.filesChanged} file{entry.filesChanged !== 1 ? "s" : ""}</span>
                                {entry.totalAcknowledged > 0 && (
                                    <>
                                        <span className="text-white/15">·</span>
                                        <span className="flex items-center gap-1">
                                            <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400/70" />
                                            {entry.acknowledgedCount}/{entry.totalAcknowledged} confirmed
                                        </span>
                                    </>
                                )}
                                <StrictnessBadge mode={entry.strictnessMode} />
                            </div>

                            {/* Affected components */}
                            {entry.affectedComponents.length > 0 && (
                                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                                    <span className="text-[10px] text-white/25">propagated to</span>
                                    {entry.affectedComponents.map(c => (
                                        <span key={c} className="text-[10px] text-white/50 bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded-full">
                                            {c}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 ml-2 shrink-0">
                            {!entry.isRestore && (
                                <button
                                    id={`restore-btn-${entry.id}`}
                                    onClick={() => onRestore(entry)}
                                    className="flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white border border-white/[0.06] hover:border-white/20 px-2.5 py-1.5 rounded-lg transition-colors"
                                >
                                    <RotateCcw className="h-3 w-3" />
                                    Restore
                                </button>
                            )}
                            <button
                                id={`toggle-diff-${entry.id}`}
                                onClick={() => setExpanded(v => !v)}
                                className="flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white border border-white/[0.06] hover:border-white/20 px-2.5 py-1.5 rounded-lg transition-colors"
                            >
                                {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                                {expanded ? "Hide diff" : "View diff"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Inline diff (expandable) */}
                {expanded && (
                    <div className="border-t border-white/[0.06]">
                        <div className="flex items-center gap-2 px-5 py-2 bg-black/30">
                            <span className="text-[10px] font-mono text-white/35">{entry.diff.filename}</span>
                        </div>
                        <div style={{ height: 220 }}>
                            <DiffEditor
                                height={220}
                                theme="vs-dark"
                                language="typescript"
                                original={entry.diff.original}
                                modified={entry.diff.modified}
                                options={{
                                    readOnly: true,
                                    fontSize: 12,
                                    lineHeight: 19,
                                    renderSideBySide: false,
                                    minimap: { enabled: false },
                                    scrollBeyondLastLine: false,
                                    wordWrap: "on",
                                    fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, monospace",
                                    padding: { top: 8, bottom: 8 },
                                }}
                                loading={<div className="flex items-center justify-center h-full bg-[#1e1e1e]"><Loader2 className="h-4 w-4 text-white/20 animate-spin" /></div>}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

interface VersionHistoryPageProps {
    projectId: string;
    onBack: () => void;
    onReviewChange: (projectId: string, changeId: string) => void;
}

export const VersionHistoryPage = ({ projectId, onBack, onReviewChange }: VersionHistoryPageProps) => {
    const [search, setSearch] = useState("");
    const [componentFilter, setComponentFilter] = useState("all");
    const [restoreTarget, setRestoreTarget] = useState<HistoryEntry | null>(null);
    const [restored, setRestored] = useState<string[]>([]);
    const [visibleCount, setVisibleCount] = useState(4);
    const [loadingMore, setLoadingMore] = useState(false);

    const components = ["all", ...Array.from(new Set(MOCK_HISTORY.map(h => h.component)))];

    const filtered = MOCK_HISTORY.filter(h => {
        const matchSearch = !search || h.title.toLowerCase().includes(search.toLowerCase()) || h.author.name.toLowerCase().includes(search.toLowerCase());
        const matchComponent = componentFilter === "all" || h.component === componentFilter;
        return matchSearch && matchComponent;
    });

    const visible = filtered.slice(0, visibleCount);

    const handleLoadMore = () => {
        setLoadingMore(true);
        setTimeout(() => { setVisibleCount(v => v + 3); setLoadingMore(false); }, 700);
    };

    const handleConfirmRestore = () => {
        if (restoreTarget) setRestored(prev => [...prev, restoreTarget.id]);
        setRestoreTarget(null);
    };

    // Stats
    const totalMerges = MOCK_HISTORY.filter(h => !h.isRestore).length;
    const totalRestores = MOCK_HISTORY.filter(h => h.isRestore).length;
    const uniqueContributors = new Set(MOCK_HISTORY.map(h => h.author.name)).size;

    return (
        <div className="flex h-screen bg-black text-white overflow-hidden flex-col relative">
            <div className="fixed inset-0 z-0 pointer-events-none">
                <Particles quantity={80} className="absolute inset-0 h-full w-full" color="#ffffff" staticity={90} size={0.25} />
            </div>

            <div className="relative z-10 flex flex-col h-full">

                {/* ── Header ─────────────────────────────────────────────────────── */}
                <header className="shrink-0 flex items-center justify-between px-6 py-3 border-b border-white/[0.06] bg-black/40 backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                        <div className="h-6 w-6 rounded-md bg-white flex items-center justify-center">
                            <Waves className="h-3.5 w-3.5 text-black" />
                        </div>
                        <button
                            id="history-back-btn"
                            onClick={onBack}
                            className="flex items-center gap-1.5 text-white/40 hover:text-white transition-colors text-sm"
                        >
                            <ArrowLeft className="h-3.5 w-3.5" />
                            Project
                        </button>
                        <span className="text-white/20">/</span>
                        <div className="flex items-center gap-2">
                            <History className="h-4 w-4 text-white/50" />
                            <span className="text-sm font-semibold text-white">Version History</span>
                        </div>
                    </div>

                    {/* Summary stats */}
                    <div className="flex items-center gap-5 text-[11px] text-white/30">
                        <span className="flex items-center gap-1.5">
                            <GitMerge className="h-3 w-3 text-emerald-400/60" />
                            {totalMerges} merges
                        </span>
                        <span className="flex items-center gap-1.5">
                            <RotateCcw className="h-3 w-3 text-amber-400/60" />
                            {totalRestores} restore{totalRestores !== 1 ? "s" : ""}
                        </span>
                        <span className="flex items-center gap-1.5">
                            <Users className="h-3 w-3 text-white/30" />
                            {uniqueContributors} contributors
                        </span>
                    </div>
                </header>

                {/* ── Filter Bar ─────────────────────────────────────────────────── */}
                <div className="shrink-0 flex items-center gap-3 px-6 py-3 border-b border-white/[0.04] bg-black/20">
                    {/* Search */}
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/20" />
                        <input
                            id="history-search"
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Search changes..."
                            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                        />
                        {search && (
                            <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/20 hover:text-white">
                                <X className="h-3 w-3" />
                            </button>
                        )}
                    </div>

                    {/* Component filter pills */}
                    <div className="flex items-center gap-1.5 overflow-x-auto">
                        <Filter className="h-3.5 w-3.5 text-white/20 shrink-0" />
                        {components.map(c => (
                            <button
                                key={c}
                                onClick={() => setComponentFilter(c)}
                                className={cn(
                                    "px-3 py-1 text-[11px] font-medium rounded-full border transition-colors whitespace-nowrap",
                                    componentFilter === c
                                        ? "bg-white/10 border-white/20 text-white"
                                        : "border-white/[0.06] text-white/30 hover:text-white/60 hover:border-white/15"
                                )}
                            >
                                {c === "all" ? "All components" : c}
                            </button>
                        ))}
                    </div>
                </div>

                {/* ── Timeline ───────────────────────────────────────────────────── */}
                <main className="flex-1 overflow-y-auto px-6 py-6">
                    {filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-48 text-center">
                            <History className="h-8 w-8 text-white/15 mb-3" />
                            <p className="text-sm text-white/30">No matching history entries</p>
                            <button onClick={() => { setSearch(""); setComponentFilter("all"); }} className="mt-2 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                                Clear filters
                            </button>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto">
                            {/* Today / Earlier grouping */}
                            {visible.map((entry, i) => (
                                <div key={entry.id}>
                                    {/* Date group label */}
                                    {(i === 0 || (i > 0 && entry.mergedAtRelative !== visible[i - 1].mergedAtRelative && ["28 min ago", "5 hours ago"].includes(entry.mergedAtRelative))) && i === 0 && (
                                        <div className="flex items-center gap-3 mb-4 ml-12">
                                            <span className="text-[10px] font-semibold text-white/25 uppercase tracking-wider">Recent</span>
                                            <div className="flex-1 h-px bg-white/[0.04]" />
                                        </div>
                                    )}
                                    {entry.mergedAtRelative === "Yesterday" && i > 0 && visible[i - 1].mergedAtRelative !== "Yesterday" && (
                                        <div className="flex items-center gap-3 my-4 ml-12">
                                            <span className="text-[10px] font-semibold text-white/25 uppercase tracking-wider">Earlier</span>
                                            <div className="flex-1 h-px bg-white/[0.04]" />
                                        </div>
                                    )}
                                    <div className={cn(restored.includes(entry.id) ? "opacity-50 pointer-events-none" : "")}>
                                        <HistoryCard
                                            entry={entry}
                                            isFirst={i === 0}
                                            isLast={i === visible.length - 1}
                                            onRestore={setRestoreTarget}
                                        />
                                    </div>
                                </div>
                            ))}

                            {/* Load more */}
                            {filtered.length > visibleCount && (
                                <div className="flex justify-center mt-2 ml-12">
                                    <button
                                        id="load-more-btn"
                                        onClick={handleLoadMore}
                                        disabled={loadingMore}
                                        className="flex items-center gap-2 px-4 py-2 text-xs text-white/40 hover:text-white border border-white/[0.06] hover:border-white/20 rounded-xl transition-colors"
                                    >
                                        {loadingMore ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ChevronDown className="h-3.5 w-3.5" />}
                                        {loadingMore ? "Loading..." : `${filtered.length - visibleCount} more entries`}
                                    </button>
                                </div>
                            )}

                            {/* End of history */}
                            {visibleCount >= filtered.length && filtered.length > 0 && (
                                <div className="flex items-center gap-3 mt-4 ml-12">
                                    <div className="flex-1 h-px bg-white/[0.04]" />
                                    <span className="text-[10px] text-white/20">Start of history</span>
                                    <div className="flex-1 h-px bg-white/[0.04]" />
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>

            {/* Restore modal */}
            {restoreTarget && (
                <RestoreModal
                    entry={restoreTarget}
                    onConfirm={handleConfirmRestore}
                    onCancel={() => setRestoreTarget(null)}
                />
            )}
        </div>
    );
};
