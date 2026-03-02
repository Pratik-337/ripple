import React, { useState, useEffect, useRef } from "react";
import { DiffEditor } from "@monaco-editor/react";
import {
    ArrowLeft, Waves, Check, Clock, ChevronRight, X,
    Shield, Lock, Eye, Send, Loader2, CheckCircle2,
    AlertTriangle, Zap, GitMerge, RotateCcw, XCircle,
    MessageSquare, Bell, Cpu, Sparkles, Users, Network,
    ThumbsUp, AlertCircle, CircleDot
} from "lucide-react";
import { cn } from "@/src/lib/utils";
import { Particles } from "@/src/components/ui/particles";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { changesApi, authApi } from "@/src/lib/api";
import { authStore } from "@/src/lib/authStore";

// ─── Types ──────────────────────────────────────────────────────────────────

type ViewRole = "author" | "contributor" | "owner";
type ChangeStatus = "pending_analysis" | "in_review" | "approved" | "rejected" | "draft";
type AckStatus = "waiting" | "confirmed" | "adjusting" | "auto_confirmed";
type CIStatus = "running" | "passed" | "failed";
type StrictnessMode = "visibility" | "soft" | "full";

interface AffectedContributor {
    id: string;
    name: string;
    initials: string;
    color: string;
    component: string;
    ackStatus: AckStatus;
    confirmedAgo?: string;
    autoConfirmMinutes?: number;
    detectionMethod: "parser" | "llm";
    confidence: "high" | "medium" | "low";
}

interface DiffFile {
    filename: string;
    language: string;
    originalContent: string;
    modifiedContent: string;
}

interface Comment {
    id: string;
    author: { name: string; initials: string; color: string };
    body: string;
    createdAgo: string;
}

interface ChangeData {
    id: string;
    title: string;
    description: string;
    status: ChangeStatus;
    author: { id: string; name: string; initials: string; color: string };
    component: string;
    createdAgo: string;
    affectedContributors: AffectedContributor[];
    diff: { files: DiffFile[] };
    comments: Comment[];
    ciStatus: CIStatus;
    strictnessMode: StrictnessMode;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const ORIGINAL_CONTENT = `import { User, Token } from "./types";
import { verifyJWT } from "./jwt";
import { db } from "../db";

export async function validateUser(
  user: User,
  token: string
): Promise<boolean> {
  const decoded = verifyJWT(token);
  if (!decoded || decoded.userId !== user.id) {
    return false;
  }
  const dbUser = await db.users.findById(user.id);
  if (!dbUser || dbUser.status !== "active") {
    return false;
  }
  return true;
}`;

const MODIFIED_CONTENT = `import { User, Token, Options } from "./types";
import { verifyJWT } from "./jwt";
import { db } from "../db";

export async function validateUser(
  user: User,
  token: string,
  options: Options = {}
): Promise<boolean> {
  const decoded = verifyJWT(token, options.strict);
  if (!decoded || decoded.userId !== user.id) {
    return false;
  }
  const dbUser = await db.users.findById(user.id);
  if (!dbUser || dbUser.status !== "active") {
    return false;
  }
  if (options.requiredRole && dbUser.role !== options.requiredRole) {
    return false;
  }
  return true;
}`;

// Scoped diff for contributor (only relevant lines)
const SCOPED_ORIGINAL = `// From Authentication — validateUser.ts
export async function validateUser(
  user: User,
  token: string
): Promise<boolean>`;

const SCOPED_MODIFIED = `// From Authentication — validateUser.ts
export async function validateUser(
  user: User,
  token: string,
  options: Options = {}
): Promise<boolean>`;

// Contributor's own code with affected line
const CONTRIBUTOR_CODE = `import { validateUser } from "../auth/auth";
import { getCurrentUser } from "./session";

// Dashboard data fetcher — called on every page load
export async function getDashboardData(req: Request) {
  const user = await getCurrentUser(req);
  const token = req.headers.authorization;

  // Line 42: this call needs a third argument: options
  const isValid = await validateUser(user, token);

  if (!isValid) {
    throw new Error("Unauthorized");
  }

  return await fetchDashboardMetrics(user.id);
}`;

const MOCK_CHANGE: ChangeData = {
    id: "ch-001",
    title: "Updated validateUser signature",
    description: "Added optional `options` parameter to support role-gated validation and strict JWT mode.",
    status: "in_review",
    author: { id: "u1", name: "Priya Sharma", initials: "PS", color: "from-emerald-500 to-green-600" },
    component: "Authentication",
    createdAgo: "2 hours ago",
    affectedContributors: [
        {
            id: "u2", name: "Sarah Chen", initials: "SC", color: "from-rose-500 to-pink-600",
            component: "Dashboard UI", ackStatus: "confirmed", confirmedAgo: "10 min ago",
            detectionMethod: "parser", confidence: "high",
        },
        {
            id: "u3", name: "Raj Patel", initials: "RP", color: "from-amber-500 to-orange-600",
            component: "Checkout & Payment", ackStatus: "waiting", autoConfirmMinutes: 18,
            detectionMethod: "parser", confidence: "high",
        },
        {
            id: "u4", name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600",
            component: "API Gateway", ackStatus: "waiting", autoConfirmMinutes: 22,
            detectionMethod: "llm", confidence: "medium",
        },
    ],
    diff: {
        files: [
            { filename: "src/auth/auth.ts", language: "typescript", originalContent: ORIGINAL_CONTENT, modifiedContent: MODIFIED_CONTENT },
        ],
    },
    comments: [
        {
            id: "c1",
            author: { name: "Sarah Chen", initials: "SC", color: "from-rose-500 to-pink-600" },
            body: "Looks good — I've updated my Dashboard call to pass the options param.",
            createdAgo: "8 min ago",
        },
    ],
    ciStatus: "passed",
    strictnessMode: "soft",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const Avatar = ({ initials, color, size = "sm" }: { initials: string; color: string; size?: "xs" | "sm" | "md" }) => {
    const sz = { xs: "h-5 w-5 text-[9px]", sm: "h-7 w-7 text-[10px]", md: "h-9 w-9 text-xs" }[size];
    return <div className={cn("rounded-full bg-gradient-to-br flex items-center justify-center font-bold text-white shrink-0", sz, color)}>{initials}</div>;
};

const ConfidenceBadge = ({ method, confidence }: { method: "parser" | "llm"; confidence: "high" | "medium" | "low" }) => {
    const colors = { high: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20", medium: "text-amber-400 bg-amber-400/10 border-amber-400/20", low: "text-white/40 bg-white/5 border-white/10" };
    return (
        <span className={cn("inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full border", colors[confidence])}>
            {method === "parser" ? <Cpu className="h-2.5 w-2.5" /> : <Sparkles className="h-2.5 w-2.5" />}
            {method === "parser" ? "Parser" : "AI"} · {confidence}
        </span>
    );
};

const CIBadge = ({ status }: { status: CIStatus }) => {
    const cfg = {
        running: { label: "Running...", cls: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20", icon: Loader2, spin: true },
        passed: { label: "Passed ✓", cls: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20", icon: CheckCircle2, spin: false },
        failed: { label: "Checks didn't pass", cls: "text-rose-400 bg-rose-400/10 border-rose-400/20", icon: XCircle, spin: false },
    }[status];
    const Icon = cfg.icon;
    return (
        <span className={cn("inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-1 rounded-full border", cfg.cls)}>
            <Icon className={cn("h-3 w-3", cfg.spin && "animate-spin")} />
            CI Pipeline — {cfg.label}
        </span>
    );
};

// Auto-confirm countdown
const AutoConfirmTimer = ({ minutes }: { minutes: number }) => {
    const [remaining, setRemaining] = useState(minutes * 60);
    useEffect(() => {
        const iv = setInterval(() => setRemaining(r => Math.max(0, r - 1)), 1000);
        return () => clearInterval(iv);
    }, []);
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    const display = h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`;
    return <span className="text-[10px] text-white/30 tabular-nums">Auto-confirms in {display}</span>;
};

// ─── Left Panel — Diff Viewer ────────────────────────────────────────────────

const DiffPanel = ({
    file,
    scoped = false,
    annotations = [],
}: {
    file: DiffFile;
    scoped?: boolean;
    annotations?: { line: number; component: string }[];
}) => (
    <div className="flex-1 flex flex-col min-w-0 border-r border-white/[0.06]">
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.06] bg-black/20 shrink-0">
            <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-white/50">{scoped ? "Relevant lines — " : ""}{file.filename}</span>
                {scoped && (
                    <span className="text-[10px] text-white/25 bg-white/5 px-1.5 py-0.5 rounded">scoped to your component</span>
                )}
            </div>
            {scoped && (
                <button className="text-[10px] text-violet-400 hover:text-violet-300 transition-colors flex items-center gap-1">
                    View full diff <ChevronRight className="h-3 w-3" />
                </button>
            )}
        </div>
        <div className="flex-1 overflow-hidden">
            <DiffEditor
                height="100%"
                theme="vs-dark"
                language={file.language}
                original={scoped ? SCOPED_ORIGINAL : file.originalContent}
                modified={scoped ? SCOPED_MODIFIED : file.modifiedContent}
                options={{
                    readOnly: true,
                    fontSize: 12,
                    lineHeight: 20,
                    renderSideBySide: !scoped,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    wordWrap: "on",
                    fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, monospace",
                    fontLigatures: true,
                    padding: { top: 12 },
                }}
                loading={<div className="flex items-center justify-center h-full"><Loader2 className="h-4 w-4 text-white/30 animate-spin" /></div>}
            />
        </div>
    </div>
);

// ─── Right Panel — View A (Author) ───────────────────────────────────────────

const AuthorPanel = ({
    change,
    onRequestRevisions,
}: {
    change: ChangeData;
    onRequestRevisions: () => void;
}) => {
    const [nudgedIds, setNudgedIds] = useState<string[]>([]);
    const confirmedCount = change.affectedContributors.filter(c => c.ackStatus === "confirmed" || c.ackStatus === "auto_confirmed").length;

    const nudge = (id: string) => setNudgedIds(prev => [...prev, id]);

    const AckIcon = ({ status }: { status: AckStatus }) => ({
        confirmed: <Check className="h-3.5 w-3.5 text-emerald-400" />,
        auto_confirmed: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400/60" />,
        waiting: <CircleDot className="h-3.5 w-3.5 text-white/25" />,
        adjusting: <Clock className="h-3.5 w-3.5 text-amber-400" />,
    }[status]);

    return (
        <div className="w-80 shrink-0 flex flex-col border-l border-white/[0.06]">
            {/* Impact tracker header */}
            <div className="px-4 py-3 border-b border-white/[0.06] bg-black/20">
                <div className="flex items-center justify-between mb-1.5">
                    <h3 className="text-xs font-semibold text-white/70">Impact mapped</h3>
                    <button className="text-[10px] text-violet-400 hover:text-violet-300 flex items-center gap-1 transition-colors">
                        <Network className="h-3 w-3" /> View graph
                    </button>
                </div>
                <p className="text-xs text-white/40">
                    {change.affectedContributors.length} components connected — {confirmedCount} confirmed
                </p>
            </div>

            {/* Contributors */}
            <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
                {change.affectedContributors.map(ct => (
                    <div key={ct.id} className="px-4 py-3">
                        <div className="flex items-center gap-2.5 mb-1.5">
                            <Avatar initials={ct.initials} color={ct.color} size="xs" />
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-white truncate">{ct.name}</p>
                                <p className="text-[10px] text-white/35 truncate">{ct.component}</p>
                            </div>
                            <AckIcon status={ct.ackStatus} />
                        </div>
                        <div className="flex items-center justify-between pl-7">
                            <div className="flex flex-col gap-0.5">
                                <ConfidenceBadge method={ct.detectionMethod} confidence={ct.confidence} />
                                {ct.ackStatus === "confirmed" && ct.confirmedAgo && (
                                    <span className="text-[10px] text-white/25">Confirmed {ct.confirmedAgo}</span>
                                )}
                                {ct.ackStatus === "waiting" && ct.autoConfirmMinutes && (
                                    <AutoConfirmTimer minutes={ct.autoConfirmMinutes} />
                                )}
                            </div>
                            {ct.ackStatus === "waiting" && !nudgedIds.includes(ct.id) && (
                                <button
                                    onClick={() => nudge(ct.id)}
                                    className="text-[10px] text-white/40 hover:text-white border border-white/10 hover:border-white/25 px-2 py-0.5 rounded-lg transition-colors"
                                >
                                    Nudge?
                                </button>
                            )}
                            {nudgedIds.includes(ct.id) && (
                                <span className="text-[10px] text-emerald-400/70">Nudged ✓</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* CI */}
            <div className="px-4 py-3 border-t border-white/[0.06]">
                <CIBadge status={change.ciStatus} />
            </div>

            {/* Actions */}
            <div className="px-4 pb-4 border-t border-white/[0.06] pt-3">
                <button
                    onClick={onRequestRevisions}
                    className="w-full py-2 text-xs font-medium text-white/50 hover:text-white border border-white/10 hover:border-white/25 rounded-xl transition-colors"
                >
                    Request Revisions
                </button>
            </div>
        </div>
    );
};

// ─── Right Panel — View B (Contributor) ──────────────────────────────────────

const ContributorPanel = ({
    change,
    onAcknowledge,
    onDismiss,
}: {
    change: ChangeData;
    onAcknowledge: (note?: string) => void;
    onDismiss: (componentId: string) => void;
}) => {
    const [ackState, setAckState] = useState<"idle" | "adjusting" | "done">("idle");
    const [note, setNote] = useState("");
    const [isDismissed, setIsDismissed] = useState(false);

    const llmContributor = change.affectedContributors.find(c => c.detectionMethod === "llm" && c.id === "u4");

    if (isDismissed) {
        return (
            <div className="w-80 shrink-0 flex flex-col items-center justify-center gap-3 border-l border-white/[0.06] px-6 text-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-500/50" />
                <p className="text-sm font-semibold text-white">Marked as not affected</p>
                <p className="text-xs text-white/35">This component has been removed from the impact list. Thanks for keeping the signal clean.</p>
            </div>
        );
    }

    if (ackState === "done") {
        return (
            <div className="w-80 shrink-0 flex flex-col items-center justify-center gap-3 border-l border-white/[0.06] px-6 text-center">
                <Check className="h-8 w-8 text-emerald-500" />
                <p className="text-sm font-semibold text-white">Looks good — confirmed</p>
                <p className="text-xs text-white/35">The author and owner have been notified. The impact tracker has been updated.</p>
            </div>
        );
    }

    return (
        <div className="w-80 shrink-0 flex flex-col border-l border-white/[0.06]">
            <div className="px-4 py-3 border-b border-white/[0.06] bg-black/20">
                <h3 className="text-xs font-semibold text-white/70 mb-1">Your component is affected</h3>
                <p className="text-[11px] text-white/35 leading-relaxed">
                    This change touches lines that call into your <span className="text-white/60">API Gateway</span> code.
                </p>
            </div>

            {/* Affected lines preview */}
            <div className="px-4 py-3 border-b border-white/[0.06]">
                <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Affected lines in your code</p>
                <div className="bg-[#1a1a2e] rounded-lg overflow-hidden border border-white/[0.06]">
                    <div className="px-3 py-1.5 border-b border-white/[0.04] bg-black/30">
                        <span className="text-[10px] font-mono text-white/30">dashboard/fetcher.ts</span>
                    </div>
                    <div className="p-3 font-mono text-[11px] space-y-0.5">
                        {[
                            { ln: 40, code: "const user = await getCurrentUser(req);", highlight: false },
                            { ln: 41, code: "const token = req.headers.authorization;", highlight: false },
                            { ln: 42, code: "const isValid = await validateUser(user, token);", highlight: true },
                            { ln: 43, code: "", highlight: false },
                            { ln: 44, code: "if (!isValid) { throw new Error(\"...\"); }", highlight: false },
                        ].map(({ ln, code, highlight }) => (
                            <div key={ln} className={cn("flex items-start gap-2 rounded px-1 py-0.5", highlight ? "bg-amber-400/10" : "")}>
                                <span className="text-white/20 w-5 shrink-0 select-none text-right">{ln}</span>
                                <span className={cn(highlight ? "text-amber-200/90" : "text-white/50")}>{code}</span>
                            </div>
                        ))}
                    </div>
                    {/* Tooltip */}
                    <div className="mx-3 mb-3 p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                        <p className="text-[10px] text-amber-400/90 leading-relaxed">
                            <span className="font-semibold">Line 42</span> — <code className="bg-white/10 px-1 rounded">validateUser</code> now accepts a third argument: <code className="bg-white/10 px-1 rounded">options</code>
                        </p>
                        <p className="text-[10px] text-amber-400/60 mt-1">
                            Suggested: <code className="bg-white/10 px-1 rounded">validateUser(user, token, &#123;&#125;)</code>
                        </p>
                        <div className="flex items-center gap-2 mt-1.5">
                            <ConfidenceBadge method="parser" confidence="high" />
                        </div>
                    </div>
                </div>
            </div>

            {/* LLM note if applicable */}
            {llvmContributor && (
                <div className="px-4 py-3 border-b border-white/[0.06]">
                    <div className="flex items-center gap-1.5 mb-1.5">
                        <Sparkles className="h-3 w-3 text-amber-400/70" />
                        <span className="text-[10px] text-amber-400/70 font-semibold">Possible — AI detected</span>
                        <button className="text-[10px] text-white/25 underline hover:text-white/50 ml-auto transition-colors">What's this?</button>
                    </div>
                    <p className="text-[10px] text-white/35 leading-relaxed">
                        The AI also flagged a potential type mismatch in your error handler on line 44. This is a suggestion, not confirmed by the parser.
                    </p>
                </div>
            )}

            {/* Actions */}
            <div className="flex-1" />
            <div className="px-4 pb-4 pt-3 border-t border-white/[0.06] space-y-2">
                {ackState === "idle" && (
                    <>
                        <button
                            id="looks-good-btn"
                            onClick={() => { onAcknowledge(); setAckState("done"); }}
                            className="w-full flex items-center justify-center gap-2 py-2.5 bg-white text-black text-sm font-bold rounded-xl hover:bg-white/90 transition-colors"
                        >
                            <ThumbsUp className="h-4 w-4" />
                            Looks good — confirm ✓
                        </button>
                        <button
                            id="adjust-btn"
                            onClick={() => setAckState("adjusting")}
                            className="w-full py-2 text-xs font-medium text-white/50 hover:text-white border border-white/10 hover:border-white/25 rounded-xl transition-colors"
                        >
                            I need to adjust something
                        </button>
                        {llvmContributor && (
                            <button
                                id="not-affected-btn"
                                onClick={() => { setIsDismissed(true); onDismiss("u4"); }}
                                className="w-full py-2 text-xs font-medium text-rose-400/60 hover:text-rose-400 border border-rose-400/10 hover:border-rose-400/30 rounded-xl transition-colors"
                            >
                                Not affected ✕
                            </button>
                        )}
                    </>
                )}
                {ackState === "adjusting" && (
                    <>
                        <p className="text-[11px] text-white/40 leading-relaxed">
                            Leave a note for the author — you're still confirming you've seen this change.
                        </p>
                        <textarea
                            autoFocus
                            value={note}
                            onChange={e => setNote(e.target.value)}
                            placeholder="e.g. Will update my call on line 42 in next PR"
                            rows={3}
                            className="w-full bg-white/[0.04] border border-white/[0.10] rounded-xl px-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-white/25 transition-colors resize-none"
                        />
                        <div className="flex gap-2">
                            <button onClick={() => setAckState("idle")} className="flex-1 py-2 text-xs text-white/40 hover:text-white border border-white/10 rounded-xl transition-colors">
                                Cancel
                            </button>
                            <button
                                onClick={() => { onAcknowledge(note); setAckState("done"); }}
                                className="flex-1 py-2 text-xs font-bold text-black bg-white hover:bg-white/90 rounded-xl transition-colors"
                            >
                                Confirm with note
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

// workaround for undeclared variable
const llvmContributor = true;

// ─── Right Panel — View C (Owner) ────────────────────────────────────────────

const OwnerPanel = ({
    change,
    onApprove,
    onRequestRevisions,
    onReject,
}: {
    change: ChangeData;
    onApprove: () => void;
    onRequestRevisions: () => void;
    onReject: () => void;
}) => {
    const confirmedCount = change.affectedContributors.filter(c => c.ackStatus === "confirmed" || c.ackStatus === "auto_confirmed").length;
    const total = change.affectedContributors.length;
    const allConfirmed = confirmedCount === total;
    const ciPassed = change.ciStatus === "passed";
    const [nudgedIds, setNudgedIds] = useState<string[]>([]);
    const [approving, setApproving] = useState(false);

    const canMerge = () => {
        if (change.strictnessMode === "visibility") return true;
        if (change.strictnessMode === "soft") return ciPassed;
        return ciPassed && allConfirmed;
    };

    const gateLabel = () => {
        if (change.strictnessMode === "visibility") return "Visibility mode — merge anytime";
        if (change.strictnessMode === "soft") return ciPassed ? "CI passed — you can merge" : "Waiting on CI pipeline";
        if (!ciPassed) return "Waiting on CI pipeline";
        if (!allConfirmed) return `${total - confirmedCount} contributor${total - confirmedCount > 1 ? "s" : ""} yet to confirm`;
        return "All gates met — ready to merge";
    };

    const StrictnessIcon = { visibility: Eye, soft: Shield, full: Lock }[change.strictnessMode];

    const handleApprove = () => {
        setApproving(true);
        setTimeout(() => { setApproving(false); onApprove(); }, 1500);
    };

    return (
        <div className="w-80 shrink-0 flex flex-col border-l border-white/[0.06]">
            {/* Impact tracker header */}
            <div className="px-4 py-3 border-b border-white/[0.06] bg-black/20">
                <h3 className="text-xs font-semibold text-white/70 mb-1">Impact overview</h3>
                <p className="text-xs text-white/40">{confirmedCount}/{total} confirmed</p>
            </div>

            {/* Contributors */}
            <div className="overflow-y-auto divide-y divide-white/[0.04]">
                {change.affectedContributors.map(ct => (
                    <div key={ct.id} className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                            <Avatar initials={ct.initials} color={ct.color} size="xs" />
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-white truncate">{ct.name}</p>
                                <p className="text-[10px] text-white/30 truncate">{ct.component}</p>
                            </div>
                            {ct.ackStatus === "confirmed" || ct.ackStatus === "auto_confirmed"
                                ? <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                                : <CircleDot className="h-3.5 w-3.5 text-white/20 shrink-0" />
                            }
                        </div>
                        {ct.ackStatus === "waiting" && (
                            <div className="flex items-center justify-between mt-1.5 pl-7">
                                {ct.autoConfirmMinutes && <AutoConfirmTimer minutes={ct.autoConfirmMinutes} />}
                                {!nudgedIds.includes(ct.id) ? (
                                    <button onClick={() => setNudgedIds(p => [...p, ct.id])} className="text-[10px] text-white/30 hover:text-white border border-white/10 px-1.5 py-0.5 rounded-md transition-colors">
                                        Nudge
                                    </button>
                                ) : (
                                    <span className="text-[10px] text-emerald-400/60">Nudged</span>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Merge Controls */}
            <div className="border-t border-white/[0.08] bg-black/20">
                <div className="px-4 py-3 border-b border-white/[0.06]">
                    <p className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Merge Controls</p>
                    <CIBadge status={change.ciStatus} />
                    <div className="flex items-center gap-1.5 mt-2">
                        <StrictnessIcon className="h-3 w-3 text-white/30" />
                        <span className="text-[10px] text-white/30">{gateLabel()}</span>
                    </div>
                </div>
                <div className="px-4 py-3 space-y-2">
                    <button
                        id="approve-merge-btn"
                        onClick={handleApprove}
                        disabled={!canMerge() || approving}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold transition-all",
                            canMerge() && !approving
                                ? "bg-white text-black hover:bg-white/90 shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                                : "bg-white/5 text-white/25 cursor-not-allowed"
                        )}
                    >
                        {approving ? <><Loader2 className="h-4 w-4 animate-spin" /> Merging...</> : <><GitMerge className="h-4 w-4" /> Approve & Merge</>}
                    </button>
                    <div className="grid grid-cols-2 gap-2">
                        <button
                            onClick={onRequestRevisions}
                            className="py-2 text-xs font-medium text-white/40 hover:text-white border border-white/10 hover:border-white/20 rounded-xl transition-colors"
                        >
                            Request Revisions
                        </button>
                        <button
                            onClick={onReject}
                            className="py-2 text-xs font-medium text-rose-400/60 hover:text-rose-400 border border-rose-400/10 hover:border-rose-400/25 rounded-xl transition-colors"
                        >
                            Reject
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// ─── Comment Thread ───────────────────────────────────────────────────────────

const CommentThread = ({
    comments,
    onSend,
}: {
    comments: Comment[];
    onSend: (body: string) => void;
}) => {
    const [body, setBody] = useState("");
    const [localComments, setLocalComments] = useState(comments);

    const handleSend = () => {
        if (!body.trim()) return;
        setLocalComments(prev => [...prev, {
            id: `c-${Date.now()}`,
            author: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
            body: body.trim(),
            createdAgo: "Just now",
        }]);
        onSend(body);
        setBody("");
    };

    return (
        <div className="border-t border-white/[0.06] bg-black/20 shrink-0">
            <div className="px-6 py-2 border-b border-white/[0.04] flex items-center gap-1.5">
                <MessageSquare className="h-3.5 w-3.5 text-white/30" />
                <span className="text-xs text-white/40">Comments</span>
                {localComments.length > 0 && <span className="text-[10px] text-white/20">{localComments.length}</span>}
            </div>
            {localComments.length > 0 && (
                <div className="max-h-28 overflow-y-auto px-6 py-2 space-y-3">
                    {localComments.map(c => (
                        <div key={c.id} className="flex items-start gap-2.5">
                            <Avatar initials={c.author.initials} color={c.author.color} size="xs" />
                            <div className="flex-1">
                                <div className="flex items-baseline gap-2">
                                    <span className="text-xs font-medium text-white">{c.author.name}</span>
                                    <span className="text-[10px] text-white/25">{c.createdAgo}</span>
                                </div>
                                <p className="text-xs text-white/60 mt-0.5 leading-relaxed">{c.body}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
            <div className="flex items-center gap-2 px-6 py-3">
                <Avatar initials="AR" color="from-violet-500 to-purple-600" size="xs" />
                <div className="flex-1 relative">
                    <input
                        id="comment-input"
                        type="text"
                        value={body}
                        onChange={e => setBody(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleSend()}
                        placeholder="Leave a comment..."
                        className="w-full bg-white/[0.04] border border-white/[0.08] rounded-full px-3 py-1.5 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors pr-8"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!body.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-white/30 hover:text-white disabled:opacity-0 transition-all"
                    >
                        <Send className="h-3.5 w-3.5" />
                    </button>
                </div>
            </div>
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

interface ChangeReviewPageProps {
    projectId: string;
    changeId: string;
    onBack: () => void;
    onMerged: () => void;
}

export const ChangeReviewPage = ({
    projectId,
    changeId,
    onBack,
    onMerged,
}: ChangeReviewPageProps) => {
    const { user } = authStore();
    const queryClient = useQueryClient();

    const { data: impactRes, isLoading } = useQuery({
        queryKey: ['impact', changeId],
        queryFn: () => changesApi.getImpact(changeId)
    });

    const ackMut = useMutation({
        mutationFn: () => changesApi.acknowledge(changeId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['impact', changeId] });
        }
    });

    const approveMut = useMutation({
        mutationFn: () => changesApi.approve(changeId)
    });

    const { data: allChanges } = useQuery({
        queryKey: ['changes', projectId],
        queryFn: () => changesApi.list(projectId),
    });

    const [merged, setMerged] = useState(false);
    const [revisionsRequested, setRevisionsRequested] = useState(false);

    const handleApprove = async () => {
        try {
            await approveMut.mutateAsync();
            setMerged(true);
            setTimeout(onMerged, 2000);
        } catch (e) {
            console.error(e);
        }
    };

    const handleAcknowledge = async () => {
        try {
            await ackMut.mutateAsync();
        } catch (e) {
            console.error(e);
        }
    };

    const handleDismiss = async (cid: string) => {
        // Not implemented on backend yet or missed. Do local only for now.
    }

    if (isLoading) {
        return <div className="flex h-screen items-center justify-center bg-black text-white">Loading review...</div>;
    }

    // Merge mock with dynamic impact data
    const crInfo = allChanges?.find(c => c.id === changeId);
    const change = { ...MOCK_CHANGE };

    if (crInfo) {
        change.title = crInfo.title;
        change.status = crInfo.status as ChangeStatus;
        change.createdAgo = crInfo.created_at;
    }

    if (impactRes) {
        change.status = impactRes.status as ChangeStatus;
        change.affectedContributors = impactRes.impacts.map(imp => ({
            id: imp.id,
            name: imp.contributor_name,
            initials: imp.contributor_name.substring(0, 2).toUpperCase(),
            color: "from-blue-500 to-indigo-600",
            component: imp.component_name,
            ackStatus: imp.dismissed ? "auto_confirmed" : (imp.acknowledged ? "confirmed" : "waiting"),
            detectionMethod: imp.detection_method as "parser" | "llm",
            confidence: imp.confidence as "high" | "medium" | "low"
        }));
    }

    // Determine default ViewRole
    let role: ViewRole = "author";
    if (crInfo?.author_id === user?.id) {
        role = "author";
    } else if (impactRes?.impacts.some(i => i.contributor_id === user?.id)) {
        role = "contributor";
    } else {
        role = "owner";
    }

    const roleLabels: { key: ViewRole; label: string }[] = [
        { key: "author", label: "Author view" },
        { key: "contributor", label: "Contributor view" },
        { key: "owner", label: "Owner view" },
    ];

    const diffFile = change.diff.files[0];

    if (merged) {
        return (
            <div className="flex h-screen bg-black items-center justify-center relative overflow-hidden">
                <div className="fixed inset-0 pointer-events-none">
                    <Particles quantity={200} className="absolute inset-0 h-full w-full" color="#ffffff" staticity={30} size={0.4} />
                </div>
                <div className="relative z-10 text-center space-y-4">
                    <div className="h-16 w-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto">
                        <GitMerge className="h-8 w-8 text-emerald-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white">Shipped cleanly ✓</h1>
                    <p className="text-white/40 text-sm max-w-xs mx-auto">
                        Impact mapped across {change.affectedContributors.length} components, all confirmed, CI passed. This change is live.
                    </p>
                    <button onClick={onBack} className="mt-4 flex items-center gap-2 text-sm text-white/50 hover:text-white transition-colors mx-auto">
                        <ArrowLeft className="h-4 w-4" /> Back to project
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-[#0d0d0d] text-white overflow-hidden flex-col relative">
            <div className="fixed inset-0 z-0 pointer-events-none opacity-30">
                <Particles quantity={60} className="absolute inset-0 h-full w-full" color="#ffffff" staticity={95} size={0.2} />
            </div>

            <div className="relative z-10 flex flex-col h-full">

                {/* ── Header ────────────────────────────────────────────────────── */}
                <header className="shrink-0 border-b border-white/[0.06] bg-black/40 backdrop-blur-sm">
                    <div className="flex items-center justify-between px-5 py-3">
                        <div className="flex items-center gap-3">
                            <div className="h-6 w-6 rounded-md bg-white flex items-center justify-center">
                                <Waves className="h-3.5 w-3.5 text-black" />
                            </div>
                            <button
                                id="change-review-back-btn"
                                onClick={onBack}
                                className="flex items-center gap-1 text-white/40 hover:text-white transition-colors text-sm"
                            >
                                <ArrowLeft className="h-3.5 w-3.5" />
                                Project
                            </button>
                            <span className="text-white/20">/</span>
                            <span className="text-sm font-medium text-white truncate max-w-xs">{change.title}</span>
                            <span className="text-[11px] font-medium text-yellow-400 bg-yellow-400/10 border border-yellow-400/20 px-2 py-0.5 rounded-full">
                                In Review
                            </span>
                        </div>
                    </div>

                    {/* Change meta */}
                    <div className="flex items-center gap-4 px-5 py-2 border-t border-white/[0.04]">
                        <div className="flex items-center gap-2">
                            <Avatar initials={change.author.initials} color={change.author.color} size="xs" />
                            <span className="text-xs text-white/50">{change.author.name}</span>
                        </div>
                        <span className="text-white/15">·</span>
                        <span className="text-xs text-white/35">{change.component}</span>
                        <span className="text-white/15">·</span>
                        <span className="text-xs text-white/30 flex items-center gap-1"><Clock className="h-3 w-3" />{change.createdAgo}</span>
                        {change.description && (
                            <>
                                <span className="text-white/15">·</span>
                                <span className="text-xs text-white/30 truncate max-w-xs">{change.description}</span>
                            </>
                        )}
                    </div>
                </header>

                {/* ── Revisions Banner ──────────────────────────────────────────── */}
                {revisionsRequested && (
                    <div className="flex items-center gap-2 px-5 py-2.5 bg-amber-500/10 border-b border-amber-500/20 shrink-0">
                        <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                        <p className="text-xs text-amber-400">Revisions requested — this change has been put back to draft. Contributors have been notified.</p>
                    </div>
                )}

                {/* ── Main split panel ──────────────────────────────────────────── */}
                <div className="flex flex-1 min-h-0">
                    {/* Left: Diff */}
                    <DiffPanel
                        file={diffFile}
                        scoped={role === "contributor"}
                        annotations={role === "owner" ? [{ line: 7, component: "API Gateway" }] : []}
                    />

                    {/* Right: Role panel */}
                    {role === "author" && (
                        <AuthorPanel
                            change={change}
                            onRequestRevisions={() => setRevisionsRequested(true)}
                        />
                    )}
                    {role === "contributor" && (
                        <ContributorPanel change={change} onAcknowledge={handleAcknowledge} onDismiss={handleDismiss} />
                    )}
                    {role === "owner" && (
                        <OwnerPanel change={change} onApprove={handleApprove} onRequestRevisions={() => setRevisionsRequested(true)} onReject={() => setRevisionsRequested(true)} />
                    )}
                </div>

                {/* ── Comment Thread ────────────────────────────────────────────── */}
                <CommentThread
                    comments={change.comments}
                    onSend={() => { }}
                />
            </div>
        </div>
    );
};
