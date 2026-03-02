import React, { useState, useRef, useCallback } from "react";
import {
    X, Github, FolderOpen, ChevronRight, ChevronDown, ChevronUp,
    Check, Plus, File, Folder, Trash2, Search, Users, Loader2,
    ArrowLeft, Rocket, GitBranch, Shield, Eye, Link2, Upload,
    Waves, AlertCircle, Zap, Lock
} from "lucide-react";
import { cn } from "@/src/lib/utils";
import { projectsApi, filesApi, componentsApi, notificationsApi } from "@/src/lib/api";
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

// ─── Types ────────────────────────────────────────────────────────────────────

type StrictnessMode = "visibility" | "soft" | "full";

interface WizardState {
    // Step 1
    projectName: string;
    description: string;
    strictnessMode: StrictnessMode;
    // Step 2
    sourceType: "github" | "folder" | null;
    githubUrl: string;
    githubBranch: string;
    uploadedFiles: MockFile[];
    parsingComplete: boolean;
    projectId: string | null;
    // Step 3
    components: ComponentDef[];
    // Step 4
    // (contributors stored inside components)
}

interface MockFile {
    id: string;
    name: string;
    path: string;
    language: string;
    size: string;
    componentId: string | null;
}

interface ComponentDef {
    id: string;
    name: string;
    fileIds: string[];
    contributors: ContributorAssignment[];
    color: string;
}

interface ContributorAssignment {
    id: string;
    name: string;
    initials: string;
    avatarColor: string;
    role: "contributor" | "read_only";
    email?: string;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_PARSED_FILES: MockFile[] = [
    { id: "f1", name: "auth.ts", path: "src/auth/auth.ts", language: "TypeScript", size: "4.2 KB", componentId: null },
    { id: "f2", name: "validateUser.ts", path: "src/auth/validateUser.ts", language: "TypeScript", size: "2.1 KB", componentId: null },
    { id: "f3", name: "jwt.ts", path: "src/auth/jwt.ts", language: "TypeScript", size: "1.8 KB", componentId: null },
    { id: "f4", name: "dashboard.tsx", path: "src/ui/dashboard.tsx", language: "TSX", size: "8.5 KB", componentId: null },
    { id: "f5", name: "Table.tsx", path: "src/ui/Table.tsx", language: "TSX", size: "5.2 KB", componentId: null },
    { id: "f6", name: "Chart.tsx", path: "src/ui/Chart.tsx", language: "TSX", size: "6.1 KB", componentId: null },
    { id: "f7", name: "api.ts", path: "src/api/api.ts", language: "TypeScript", size: "3.4 KB", componentId: null },
    { id: "f8", name: "routes.ts", path: "src/api/routes.ts", language: "TypeScript", size: "2.9 KB", componentId: null },
    { id: "f9", name: "middleware.ts", path: "src/api/middleware.ts", language: "TypeScript", size: "1.5 KB", componentId: null },
    { id: "f10", name: "checkout.ts", path: "src/checkout/checkout.ts", language: "TypeScript", size: "7.3 KB", componentId: null },
    { id: "f11", name: "cart.ts", path: "src/checkout/cart.ts", language: "TypeScript", size: "4.8 KB", componentId: null },
    { id: "f12", name: "payment.ts", path: "src/checkout/payment.ts", language: "TypeScript", size: "3.6 KB", componentId: null },
];

const MOCK_USERS = [
    { id: "u1", name: "Priya Sharma", initials: "PS", avatarColor: "from-emerald-500 to-green-600", email: "priya@co.com" },
    { id: "u2", name: "Raj Patel", initials: "RP", avatarColor: "from-amber-500 to-orange-600", email: "raj@co.com" },
    { id: "u3", name: "Sarah Chen", initials: "SC", avatarColor: "from-rose-500 to-pink-600", email: "sarah@co.com" },
    { id: "u4", name: "Tom Ellis", initials: "TE", avatarColor: "from-blue-500 to-indigo-600", email: "tom@co.com" },
];

const COMPONENT_COLORS = [
    "from-violet-500 to-purple-600",
    "from-blue-500 to-indigo-600",
    "from-emerald-500 to-green-600",
    "from-amber-500 to-orange-600",
    "from-rose-500 to-pink-600",
    "from-cyan-500 to-teal-600",
];

const STRICTNESS_OPTIONS: { id: StrictnessMode; label: string; sublabel: string; icon: React.ElementType; color: string }[] = [
    { id: "visibility", label: "Visibility", sublabel: "Maps impact and notifies. Merge whenever.", icon: Eye, color: "border-white/20 text-white" },
    { id: "soft", label: "Soft Enforcement", sublabel: "Auto-confirms after 24h if no response.", icon: Shield, color: "border-amber-500/40 text-amber-400" },
    { id: "full", label: "Full Governance", sublabel: "All contributors must confirm before merge.", icon: Lock, color: "border-violet-500/40 text-violet-400" },
];

// ─── Step Progress Bar ────────────────────────────────────────────────────────

const STEPS = ["Details", "Files", "Components", "Contributors", "Review"];

const ProgressBar = ({ step }: { step: number }) => (
    <div className="flex items-center gap-0 mb-8">
        {STEPS.map((label, i) => (
            <React.Fragment key={label}>
                <div className="flex flex-col items-center gap-1.5">
                    <div className={cn(
                        "h-7 w-7 rounded-full text-xs font-bold flex items-center justify-center border transition-all duration-300",
                        i < step ? "bg-white text-black border-white" :
                            i === step ? "bg-white/10 text-white border-white/40" :
                                "bg-transparent text-white/20 border-white/10"
                    )}>
                        {i < step ? <Check className="h-3.5 w-3.5" /> : i + 1}
                    </div>
                    <span className={cn("text-[10px] font-medium whitespace-nowrap", i === step ? "text-white" : "text-white/25")}>{label}</span>
                </div>
                {i < STEPS.length - 1 && (
                    <div className={cn("flex-1 h-px mb-4 mx-1 transition-all duration-500", i < step ? "bg-white/40" : "bg-white/10")} />
                )}
            </React.Fragment>
        ))}
    </div>
);

// ─── Step 1: Project Details ──────────────────────────────────────────────────

const Step1Details = ({ state, setState }: { state: WizardState; setState: React.Dispatch<React.SetStateAction<WizardState>> }) => (
    <div className="space-y-6">
        <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Project Name <span className="text-white/30">(required)</span></label>
            <input
                id="project-name-input"
                type="text"
                value={state.projectName}
                onChange={e => setState(s => ({ ...s, projectName: e.target.value }))}
                placeholder="e.g. E-Commerce Platform"
                className="w-full bg-white/[0.04] border border-white/[0.10] rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:border-white/30 transition-colors text-sm"
            />
        </div>

        <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Description <span className="text-white/30">(optional)</span></label>
            <textarea
                id="project-description-input"
                value={state.description}
                onChange={e => setState(s => ({ ...s, description: e.target.value }))}
                placeholder="What does this project do?"
                rows={3}
                className="w-full bg-white/[0.04] border border-white/[0.10] rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:border-white/30 transition-colors text-sm resize-none"
            />
        </div>

        <div>
            <label className="block text-sm font-medium text-white/70 mb-3">Strictness Mode</label>
            <div className="grid grid-cols-3 gap-3">
                {STRICTNESS_OPTIONS.map(({ id, label, sublabel, icon: Icon, color }) => (
                    <button
                        key={id}
                        id={`strictness-${id}`}
                        onClick={() => setState(s => ({ ...s, strictnessMode: id }))}
                        className={cn(
                            "group relative text-left p-4 rounded-xl border transition-all duration-200",
                            state.strictnessMode === id
                                ? "bg-white/[0.07] border-white/30"
                                : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04] hover:border-white/15"
                        )}
                    >
                        <Icon className={cn("h-4 w-4 mb-2", state.strictnessMode === id ? "text-white" : "text-white/30")} />
                        <p className={cn("text-xs font-semibold mb-1", state.strictnessMode === id ? "text-white" : "text-white/50")}>{label}</p>
                        <p className="text-[10px] text-white/25 leading-relaxed">{sublabel}</p>
                        {state.strictnessMode === id && (
                            <div className="absolute top-2.5 right-2.5 h-4 w-4 rounded-full bg-white flex items-center justify-center">
                                <Check className="h-2.5 w-2.5 text-black" />
                            </div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    </div>
);

// ─── Step 2: Source Files ─────────────────────────────────────────────────────

const FileLanguageDot = ({ lang }: { lang: string }) => {
    const colors: Record<string, string> = { TypeScript: "bg-blue-400", TSX: "bg-cyan-400", JavaScript: "bg-yellow-400", Python: "bg-green-400" };
    return <span className={cn("h-2 w-2 rounded-full shrink-0", colors[lang] ?? "bg-white/30")} />;
};

const Step2Files = ({ state, setState }: { state: WizardState; setState: React.Dispatch<React.SetStateAction<WizardState>> }) => {
    const [isParsing, setIsParsing] = useState(false);
    const [parseProgress, setParseProgress] = useState(0);
    const [showTree, setShowTree] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const uploadFilesMut = useMutation({
        mutationFn: async (files: File[]) => {
            if (!state.projectId) throw new Error("No project ID");

            // filtered
            const valid = files.filter(f => !f.webkitRelativePath.includes('node_modules/') && !f.webkitRelativePath.includes('.git/') && f.size > 0);

            setIsParsing(true);
            setParseProgress(10);

            // 1. Get presigned URLs
            const req = valid.map(f => ({
                path: f.webkitRelativePath || f.name,
                size_bytes: f.size,
                language: f.name.split('.').pop() || 'text'
            }));

            const urls = await filesApi.requestUploadUrls(state.projectId, req);
            setParseProgress(30);

            // 2. Upload each
            await Promise.all(urls.map(async (u, i) => {
                const file = valid[i];
                await axios.put(u.upload_url, file, { headers: { 'Content-Type': file.type || 'text/plain' } });
            }));
            setParseProgress(60);

            // 3. Confirm
            await filesApi.confirmBatch(state.projectId, urls.map(u => u.file_id));
            setParseProgress(90);

            // 4. Update the state
            const serverFiles = await filesApi.list(state.projectId);
            setState(s => ({
                ...s,
                uploadedFiles: serverFiles.map(f => ({
                    id: f.id,
                    name: f.path.split('/').pop() || f.path,
                    path: f.path,
                    language: f.language,
                    size: `${(f.size_bytes / 1024).toFixed(1)} KB`,
                    componentId: null
                })),
                parsingComplete: true
            }));
            setIsParsing(false);
            setParseProgress(100);
            setShowTree(true);
        }
    });

    const githubPreviewMut = useMutation({
        mutationFn: async () => {
            if (!state.projectId) throw new Error("No project ID");
            setIsParsing(true);
            setParseProgress(20);
            return await filesApi.githubPreview(state.projectId, state.githubUrl);
        },
        onSuccess: (data) => {
            setParseProgress(50);
            githubConfirmMut.mutate(data);
        },
        onError: () => setIsParsing(false)
    });

    const githubConfirmMut = useMutation({
        mutationFn: async (data: { owner: string; repo: string; files: { path: string }[] }) => {
            if (!state.projectId) throw new Error("No project ID");
            return await filesApi.githubConfirm(state.projectId, data.owner, data.repo, data.files.map(f => f.path));
        },
        onSuccess: async () => {
            setParseProgress(80);
            if (state.projectId) {
                const serverFiles = await filesApi.list(state.projectId);
                setState(s => ({
                    ...s,
                    uploadedFiles: serverFiles.map((f: any) => ({
                        id: f.id,
                        name: f.path.split('/').pop() || f.path,
                        path: f.path,
                        language: f.language,
                        size: `${(f.size_bytes / 1024).toFixed(1)} KB`,
                        componentId: null
                    })),
                    parsingComplete: true
                }));
            }
            setIsParsing(false);
            setParseProgress(100);
            setShowTree(true);
        },
        onError: () => setIsParsing(false)
    });

    const handleInputFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) uploadFilesMut.mutate(Array.from(e.target.files));
    };

    const handleGithubImport = () => {
        if (!state.githubUrl || !state.projectId) return;
        githubPreviewMut.mutate();
    };

    const handleFolderDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files) {
            uploadFilesMut.mutate(Array.from(e.dataTransfer.files));
        }
    };

    return (
        <div className="space-y-4">
            {/* Source Type Selector */}
            <div className="grid grid-cols-2 gap-3">
                {[
                    { type: "github" as const, icon: Github, label: "GitHub Repo", desc: "Import from a repository" },
                    { type: "folder" as const, icon: FolderOpen, label: "Upload Folder", desc: "Drag & drop your files" },
                ].map(({ type, icon: Icon, label, desc }) => (
                    <button
                        key={type}
                        id={`source-${type}`}
                        onClick={() => setState(s => ({ ...s, sourceType: type, parsingComplete: false, uploadedFiles: [] }))}
                        className={cn(
                            "group p-4 rounded-xl border text-left transition-all duration-200",
                            state.sourceType === type
                                ? "bg-white/[0.07] border-white/30"
                                : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04] hover:border-white/15"
                        )}
                    >
                        <Icon className={cn("h-5 w-5 mb-2 transition-colors", state.sourceType === type ? "text-white" : "text-white/30")} />
                        <p className={cn("text-sm font-semibold", state.sourceType === type ? "text-white" : "text-white/50")}>{label}</p>
                        <p className="text-[11px] text-white/25 mt-0.5">{desc}</p>
                    </button>
                ))}
            </div>

            {/* GitHub path */}
            {state.sourceType === "github" && !state.parsingComplete && (
                <div className="space-y-3">
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/20" />
                            <input
                                type="text"
                                value={state.githubUrl}
                                onChange={e => setState(s => ({ ...s, githubUrl: e.target.value }))}
                                placeholder="https://github.com/org/repo"
                                className="w-full bg-white/[0.04] border border-white/[0.10] rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-white/30 transition-colors"
                            />
                        </div>
                        <button
                            id="github-import-btn"
                            onClick={handleGithubImport}
                            disabled={!state.githubUrl || isParsing}
                            className="px-4 py-2.5 bg-white text-black text-sm font-bold rounded-xl hover:bg-white/90 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            Preview
                        </button>
                    </div>
                    <select
                        value={state.githubBranch}
                        onChange={e => setState(s => ({ ...s, githubBranch: e.target.value }))}
                        className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-sm text-white/60 focus:outline-none w-40"
                    >
                        <option value="main">main</option>
                        <option value="develop">develop</option>
                        <option value="staging">staging</option>
                    </select>
                </div>
            )}

            {/* Folder path */}
            {state.sourceType === "folder" && !state.parsingComplete && (
                <div
                    id="folder-drop-zone"
                    onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleFolderDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                        "relative flex flex-col items-center justify-center gap-3 p-10 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200",
                        dragOver ? "border-white/40 bg-white/[0.06]" : "border-white/[0.10] hover:border-white/20 hover:bg-white/[0.03]"
                    )}
                >
                    <input ref={fileInputRef} type="file" multiple {...{ webkitdirectory: "", directory: "" }} className="hidden" onChange={handleInputFiles} />
                    <Upload className={cn("h-8 w-8 transition-colors", dragOver ? "text-white" : "text-white/25")} />
                    <div className="text-center">
                        <p className="text-sm font-medium text-white/60">Drop your folder here</p>
                        <p className="text-xs text-white/25 mt-1">or click to browse — node_modules and .git are filtered automatically</p>
                    </div>
                </div>
            )}

            {/* Parsing progress */}
            {isParsing && (
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-3">
                        <Loader2 className="h-4 w-4 text-violet-400 animate-spin" />
                        <p className="text-sm text-white/70">Fetching and parsing your codebase...</p>
                    </div>
                    <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-violet-600 to-purple-500 rounded-full transition-all duration-300"
                            style={{ width: `${parseProgress}%` }}
                        />
                    </div>
                    <p className="text-[10px] text-white/25 mt-2">Running Tree-sitter across all files to extract symbols and build the dependency graph</p>
                </div>
            )}

            {/* Parsed file tree */}
            {state.parsingComplete && (
                <div className="bg-white/[0.03] border border-emerald-500/20 rounded-xl overflow-hidden">
                    <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.06] bg-emerald-500/[0.06]">
                        <Check className="h-4 w-4 text-emerald-400" />
                        <p className="text-sm font-semibold text-emerald-400">Parsed — {state.uploadedFiles.length} files ready</p>
                    </div>
                    <div className="max-h-44 overflow-y-auto divide-y divide-white/[0.04]">
                        {state.uploadedFiles.map(f => (
                            <div key={f.id} className="flex items-center gap-3 px-4 py-2">
                                <FileLanguageDot lang={f.language} />
                                <File className="h-3.5 w-3.5 text-white/25 shrink-0" />
                                <span className="text-xs text-white/60 flex-1 truncate font-mono">{f.path}</span>
                                <span className="text-[10px] text-white/25">{f.size}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// ─── Step 3: Define Components ────────────────────────────────────────────────

const Step3Components = ({ state, setState }: { state: WizardState; setState: React.Dispatch<React.SetStateAction<WizardState>> }) => {
    const [newName, setNewName] = useState("");
    const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);

    const unassignedFiles = state.uploadedFiles.filter(f => !f.componentId);
    const assignedFileIds = new Set(state.components.flatMap(c => c.fileIds));

    const toggleFile = (id: string) => {
        setSelectedFileIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
    };

    const createComponent = () => {
        if (!newName.trim() || selectedFileIds.length === 0) return;
        const colorIdx = state.components.length % COMPONENT_COLORS.length;
        const newComp: ComponentDef = {
            id: `comp-${Date.now()}`,
            name: newName.trim(),
            fileIds: selectedFileIds,
            contributors: [],
            color: COMPONENT_COLORS[colorIdx],
        };
        setState(s => ({
            ...s,
            components: [...s.components, newComp],
            uploadedFiles: s.uploadedFiles.map(f =>
                selectedFileIds.includes(f.id) ? { ...f, componentId: newComp.id } : f
            ),
        }));
        setNewName("");
        setSelectedFileIds([]);
    };

    const removeComponent = (compId: string) => {
        setState(s => ({
            ...s,
            components: s.components.filter(c => c.id !== compId),
            uploadedFiles: s.uploadedFiles.map(f => f.componentId === compId ? { ...f, componentId: null } : f),
        }));
    };

    return (
        <div className="grid grid-cols-2 gap-4 min-h-[360px]">
            {/* Left: File tree */}
            <div className="flex flex-col bg-white/[0.02] border border-white/[0.08] rounded-xl overflow-hidden">
                <div className="px-3 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
                    <span className="text-xs font-semibold text-white/50">PROJECT FILES</span>
                    {selectedFileIds.length > 0 && (
                        <span className="text-[10px] text-violet-400 font-medium">{selectedFileIds.length} selected</span>
                    )}
                </div>
                <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
                    {state.uploadedFiles.map(f => {
                        const isAssigned = !!f.componentId;
                        const isSelected = selectedFileIds.includes(f.id);
                        return (
                            <div
                                key={f.id}
                                onClick={() => !isAssigned && toggleFile(f.id)}
                                className={cn(
                                    "flex items-center gap-2.5 px-3 py-2 text-xs transition-all",
                                    isAssigned ? "opacity-30 cursor-default" :
                                        isSelected ? "bg-violet-500/10 cursor-pointer" :
                                            "cursor-pointer hover:bg-white/[0.04]"
                                )}
                            >
                                <div className={cn("h-3.5 w-3.5 rounded border flex items-center justify-center shrink-0 transition-all",
                                    isSelected ? "bg-violet-500 border-violet-500" : "border-white/20")}>
                                    {isSelected && <Check className="h-2 w-2 text-white" />}
                                </div>
                                <FileLanguageDot lang={f.language} />
                                <span className={cn("flex-1 truncate font-mono", isAssigned ? "text-white/30" : "text-white/60")}>{f.name}</span>
                                {isAssigned && (
                                    <span className="text-[9px] text-white/20 shrink-0">
                                        {state.components.find(c => c.id === f.componentId)?.name}
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
                {unassignedFiles.length === 0 && state.components.length > 0 && (
                    <div className="px-3 py-2 border-t border-white/[0.06] text-center">
                        <p className="text-[10px] text-emerald-400">✓ All files assigned</p>
                    </div>
                )}
                {unassignedFiles.length > 0 && (
                    <div className="px-3 py-2 border-t border-white/[0.06]">
                        <p className="text-[10px] text-amber-400/70">{unassignedFiles.length} files unassigned</p>
                    </div>
                )}
            </div>

            {/* Right: Components */}
            <div className="flex flex-col gap-3">
                {/* Create form */}
                <div className="bg-white/[0.02] border border-white/[0.08] rounded-xl p-3 space-y-2">
                    <input
                        id="component-name-input"
                        type="text"
                        value={newName}
                        onChange={e => setNewName(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && createComponent()}
                        placeholder="Component name (e.g. Auth)"
                        className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                    />
                    <button
                        id="create-component-btn"
                        onClick={createComponent}
                        disabled={!newName.trim() || selectedFileIds.length === 0}
                        className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-white/10 hover:bg-white/15 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg text-xs font-semibold text-white transition-colors"
                    >
                        <Plus className="h-3.5 w-3.5" />
                        Create Component
                        {selectedFileIds.length > 0 && <span className="text-white/40">({selectedFileIds.length} files)</span>}
                    </button>
                </div>

                {/* Component cards */}
                <div className="flex-1 overflow-y-auto space-y-2.5">
                    {state.components.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center py-10">
                            <GitBranch className="h-7 w-7 text-white/10 mb-2" />
                            <p className="text-xs text-white/25">Select files on the left,<br />then create your first component.</p>
                        </div>
                    ) : (
                        state.components.map((comp) => (
                            <div key={comp.id} className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <div className={cn("h-3 w-3 rounded-full bg-gradient-to-br shrink-0", comp.color)} />
                                        <span className="text-xs font-semibold text-white">{comp.name}</span>
                                    </div>
                                    <button onClick={() => removeComponent(comp.id)} className="text-white/20 hover:text-white/60 transition-colors">
                                        <Trash2 className="h-3.5 w-3.5" />
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {comp.fileIds.map(fid => {
                                        const file = state.uploadedFiles.find(f => f.id === fid);
                                        return file ? (
                                            <span key={fid} className="flex items-center gap-1 px-1.5 py-0.5 bg-white/[0.04] rounded text-[10px] text-white/40 font-mono">
                                                <FileLanguageDot lang={file.language} />
                                                {file.name}
                                            </span>
                                        ) : null;
                                    })}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

// --- Helpers ---
const generateInitials = (name?: string, email?: string) => {
    if (name) return name.substring(0, 2).toUpperCase();
    if (email) return email.substring(0, 2).toUpperCase();
    return "??";
};

const getAvatarColor = (idx: number) => {
    const colors = [
        "from-emerald-500 to-green-600",
        "from-amber-500 to-orange-600",
        "from-rose-500 to-pink-600",
        "from-blue-500 to-indigo-600",
        "from-violet-500 to-purple-600",
        "from-cyan-500 to-teal-600"
    ];
    return colors[idx % colors.length];
};

// ─── Step 4: Assign Contributors ──────────────────────────────────────────────

const Step4Contributors = ({ state, setState }: { state: WizardState; setState: React.Dispatch<React.SetStateAction<WizardState>> }) => {
    const [query, setQuery] = useState("");
    const [activeCompId, setActiveCompId] = useState<string | null>(state.components[0]?.id ?? null);

    const { data: searchResults = [] } = useQuery({
        queryKey: ['searchUsers', query],
        queryFn: () => notificationsApi.searchUsers(query),
        enabled: query.length > 1
    });

    const filtered = searchResults;

    const activeComp = state.components.find(c => c.id === activeCompId);

    const addContributor = (user: any) => {
        if (!activeCompId || !state.projectId) return;

        componentsApi.addContributor(state.projectId, activeCompId, user.id, "contributor");
        notificationsApi.createInvite(state.projectId, user.email, activeCompId);

        const color = getAvatarColor(user.id.charCodeAt(0));
        const init = generateInitials(user.name || user.display_name, user.email);

        setState(s => ({
            ...s,
            components: s.components.map(c =>
                c.id === activeCompId && !c.contributors.find(ct => ct.id === user.id)
                    ? { ...c, contributors: [...c.contributors, { id: user.id, name: user.display_name || user.name || "Unknown", initials: init, avatarColor: color, email: user.email, role: "contributor" }] }
                    : c
            ),
        }));
        setQuery("");
    };

    const removeContributor = (compId: string, userId: string) => {
        if (!state.projectId) return;
        componentsApi.removeContributor(state.projectId, compId, userId);
        setState(s => ({
            ...s,
            components: s.components.map(c =>
                c.id === compId ? { ...c, contributors: c.contributors.filter(ct => ct.id !== userId) } : c
            ),
        }));
    };

    return (
        <div className="grid grid-cols-2 gap-4 min-h-[360px]">
            {/* Left: Component list */}
            <div className="bg-white/[0.02] border border-white/[0.08] rounded-xl overflow-hidden">
                <div className="px-3 py-2.5 border-b border-white/[0.06]">
                    <span className="text-xs font-semibold text-white/50">COMPONENTS</span>
                </div>
                <div className="divide-y divide-white/[0.04]">
                    {state.components.map(comp => (
                        <div
                            key={comp.id}
                            onClick={() => setActiveCompId(comp.id)}
                            className={cn(
                                "flex items-center gap-3 px-3 py-3 cursor-pointer transition-colors",
                                activeCompId === comp.id ? "bg-white/[0.07]" : "hover:bg-white/[0.03]"
                            )}
                        >
                            <div className={cn("h-3 w-3 rounded-full bg-gradient-to-br shrink-0", comp.color)} />
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">{comp.name}</p>
                                <p className="text-[10px] text-white/30">
                                    {comp.contributors.length > 0
                                        ? `${comp.contributors.length} contributor${comp.contributors.length > 1 ? "s" : ""}`
                                        : "No contributors yet"}
                                </p>
                            </div>
                            {activeCompId === comp.id && <ChevronRight className="h-3.5 w-3.5 text-white/40" />}
                        </div>
                    ))}
                </div>
            </div>

            {/* Right: Assignment */}
            <div className="flex flex-col gap-3">
                {activeComp ? (
                    <>
                        <div className="flex items-center gap-2">
                            <div className={cn("h-3 w-3 rounded-full bg-gradient-to-br", activeComp.color)} />
                            <span className="text-sm font-semibold text-white">{activeComp.name}</span>
                        </div>

                        {/* Search */}
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/20" />
                            <input
                                type="text"
                                value={query}
                                onChange={e => setQuery(e.target.value)}
                                placeholder="Search by name or email..."
                                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                            />
                        </div>

                        {/* Search results */}
                        {filtered.length > 0 && (
                            <div className="bg-zinc-950 border border-white/10 rounded-xl overflow-hidden">
                                {filtered.map(u => (
                                    <div
                                        key={u.id}
                                        onClick={() => addContributor(u)}
                                        className="flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.05] cursor-pointer transition-colors"
                                    >
                                        <div className={cn("h-7 w-7 rounded-full bg-gradient-to-br flex items-center justify-center text-[10px] font-bold text-white", getAvatarColor(u.id.charCodeAt(0)))}>
                                            {generateInitials(u.name, u.email)}
                                        </div>
                                        <div>
                                            <p className="text-xs font-medium text-white">{u.name}</p>
                                            <p className="text-[10px] text-white/30">{u.email}</p>
                                        </div>
                                        <Plus className="h-3.5 w-3.5 text-white/30 ml-auto" />
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Assigned list */}
                        <div className="flex-1 overflow-y-auto space-y-2">
                            {/* Auto-added owner */}
                            <div className="flex items-center gap-3 px-3 py-2.5 bg-white/[0.03] rounded-xl">
                                <div className="h-7 w-7 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-[10px] font-bold text-white">Yo</div>
                                <div className="flex-1">
                                    <p className="text-xs font-medium text-white">You</p>
                                    <p className="text-[10px] text-white/30">You (owner — auto-assigned)</p>
                                </div>
                                <span className="text-[10px] text-violet-400 bg-violet-400/10 px-2 py-0.5 rounded-full font-medium">Owner</span>
                            </div>

                            {activeComp.contributors.map(ct => (
                                <div key={ct.id} className="flex items-center gap-3 px-3 py-2.5 bg-white/[0.03] rounded-xl">
                                    <div className={cn("h-7 w-7 rounded-full bg-gradient-to-br flex items-center justify-center text-[10px] font-bold text-white", ct.avatarColor)}>
                                        {ct.initials}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs font-medium text-white">{ct.name}</p>
                                    </div>
                                    <span className="text-[10px] text-white/40 bg-white/5 px-2 py-0.5 rounded-full">Contributor</span>
                                    <button onClick={() => removeContributor(activeComp.id, ct.id)} className="text-white/20 hover:text-white/60 transition-colors ml-1">
                                        <X className="h-3.5 w-3.5" />
                                    </button>
                                </div>
                            ))}

                            {activeComp.contributors.length === 0 && (
                                <p className="text-[11px] text-white/25 text-center py-6">Search for teammates above to assign them</p>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-xs text-white/25">Select a component to assign contributors</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// ─── Step 5: Review & Launch ──────────────────────────────────────────────────

const StrictnessLabels: Record<StrictnessMode, string> = { visibility: "Visibility", soft: "Soft Enforcement", full: "Full Governance" };
const StrictnessColors: Record<StrictnessMode, string> = { visibility: "text-white/60", soft: "text-amber-400", full: "text-violet-400" };

const Step5Review = ({ state }: { state: WizardState }) => {
    const totalFiles = state.components.reduce((a, c) => a + c.fileIds.length, 0);
    const totalContributors = new Set(state.components.flatMap(c => c.contributors.map(ct => ct.id))).size;

    return (
        <div className="space-y-4">
            {/* Summary header */}
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
                <h3 className="text-base font-bold text-white mb-0.5">{state.projectName || "Untitled Project"}</h3>
                {state.description && <p className="text-sm text-white/40 mb-3">{state.description}</p>}
                <div className="flex gap-4 text-xs text-white/40">
                    <span className="flex items-center gap-1.5"><GitBranch className="h-3 w-3" />{state.components.length} components</span>
                    <span className="flex items-center gap-1.5"><File className="h-3 w-3" />{totalFiles} files</span>
                    <span className="flex items-center gap-1.5"><Users className="h-3 w-3" />{totalContributors + 1} contributors</span>
                    <span className={cn("flex items-center gap-1.5 font-medium", StrictnessColors[state.strictnessMode])}>
                        <Shield className="h-3 w-3" />{StrictnessLabels[state.strictnessMode]}
                    </span>
                </div>
            </div>

            {/* Component summary list */}
            <div className="space-y-2 max-h-52 overflow-y-auto pr-0.5">
                {state.components.map(comp => (
                    <div key={comp.id} className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-3 flex items-center gap-3">
                        <div className={cn("h-3 w-3 rounded-full bg-gradient-to-br shrink-0", comp.color)} />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white">{comp.name}</p>
                            <p className="text-[10px] text-white/30 mt-0.5">{comp.fileIds.length} files</p>
                        </div>
                        <div className="flex items-center gap-1">
                            {/* Owner always shown */}
                            <div className="h-6 w-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-[9px] font-bold text-white border-2 border-black">AR</div>
                            {comp.contributors.slice(0, 3).map(ct => (
                                <div key={ct.id} className={cn("h-6 w-6 rounded-full bg-gradient-to-br flex items-center justify-center text-[9px] font-bold text-white border-2 border-black", ct.avatarColor)}>
                                    {ct.initials}
                                </div>
                            ))}
                            {comp.contributors.length > 3 && (
                                <div className="h-6 w-6 rounded-full bg-white/10 flex items-center justify-center text-[9px] text-white/60 border-2 border-black">
                                    +{comp.contributors.length - 3}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Mini graph preview placeholder */}
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 text-center">
                <div className="flex items-center justify-center gap-3 text-white/15">
                    {state.components.slice(0, 4).map((comp, i) => (
                        <React.Fragment key={comp.id}>
                            <div className={cn("h-8 w-8 rounded-lg bg-gradient-to-br opacity-50", comp.color)} />
                            {i < state.components.slice(0, 4).length - 1 && <div className="h-px w-6 bg-white/10" />}
                        </React.Fragment>
                    ))}
                </div>
                <p className="text-[10px] text-white/25 mt-3">Dependency graph will render on the project overview page</p>
            </div>

            <div className="bg-emerald-500/[0.07] border border-emerald-500/20 rounded-xl px-4 py-3 flex items-center gap-2">
                <Zap className="h-4 w-4 text-emerald-400 shrink-0" />
                <p className="text-xs text-emerald-400/80">
                    Ripple will map the full dependency graph as soon as this project goes live. Contributors will be looped in instantly.
                </p>
            </div>
        </div>
    );
};

// ─── Main Wizard Shell ────────────────────────────────────────────────────────

interface NewProjectWizardProps {
    onClose: () => void;
    onLaunch: (projectName: string) => void;
}

const INITIAL_STATE: WizardState = {
    projectName: "",
    description: "",
    strictnessMode: "visibility",
    sourceType: null,
    githubUrl: "",
    githubBranch: "main",
    uploadedFiles: [],
    parsingComplete: false,
    projectId: null,
    components: [],
};

export const NewProjectWizard = ({ onClose, onLaunch }: NewProjectWizardProps) => {
    const [step, setStep] = useState(0);
    const [state, setState] = useState<WizardState>(INITIAL_STATE);
    const [isLaunching, setIsLaunching] = useState(false);

    const canAdvance = () => {
        if (step === 0) return state.projectName.trim().length > 0;
        if (step === 1) return state.parsingComplete;
        if (step === 2) return state.components.length > 0;
        if (step === 3) return true;
        return true;
    };

    const createProjectMut = useMutation({
        mutationFn: async () => projectsApi.create(state.projectName, state.description, "from-violet-500 to-purple-600", "Activity"),
        onSuccess: (data) => {
            setState(s => ({ ...s, projectId: data.id }));
            setStep(1);
        }
    });

    const createComponentMut = useMutation({
        mutationFn: async ({ comp }: { comp: ComponentDef }) => {
            if (!state.projectId) return;
            const c = await componentsApi.create(state.projectId, comp.name, comp.color);
            await filesApi.assignToComponent(state.projectId, comp.fileIds, c.id);
            // Re-map internal id to real ID under the hood
            setState(s => ({
                ...s,
                components: s.components.map(x => x.id === comp.id ? { ...x, id: c.id } : x)
            }));
        }
    });

    const launchMut = useMutation({
        mutationFn: async () => {
            if (!state.projectId) return;
            await projectsApi.confirm(state.projectId);
            onLaunch(state.projectName);
        }
    });

    const handleNext = () => {
        if (step === 0 && !state.projectId) {
            createProjectMut.mutate();
        } else if (step === 2) {
            // Create components and assign files on the real backend when leaving step 2
            state.components.forEach(c => {
                if (c.id.startsWith("comp-")) {
                    createComponentMut.mutate({ comp: c });
                }
            });
            setStep(3);
        } else if (step < 4) {
            setStep(s => s + 1);
        }
    };

    const handleLaunch = () => {
        setIsLaunching(true);
        launchMut.mutate();
    };

    const STEP_SUBTITLES = [
        "Name your project and set how strictly Ripple manages changes.",
        "Import from GitHub or upload your project folder directly.",
        "Group your files into logical components. Ripple builds the dependency graph as you go.",
        "Assign teammates to components. They'll receive an invite and be looped in automatically.",
        "Everything looks right? Launch the project and Ripple will start mapping connections.",
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/75 backdrop-blur-md" onClick={onClose} />

            <div className="relative bg-zinc-950 border border-white/10 rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-white/[0.06] shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center">
                            <Waves className="h-4 w-4 text-black" />
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-white">New Project</h2>
                            <p className="text-xs text-white/35 mt-0.5">{STEP_SUBTITLES[step]}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-white/30 hover:text-white transition-colors mt-0.5">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Progress */}
                <div className="px-6 pt-5 shrink-0">
                    <ProgressBar step={step} />
                </div>

                {/* Step content */}
                <div className="flex-1 overflow-y-auto px-6 pb-4">
                    {step === 0 && <Step1Details state={state} setState={setState} />}
                    {step === 1 && <Step2Files state={state} setState={setState} />}
                    {step === 2 && <Step3Components state={state} setState={setState} />}
                    {step === 3 && <Step4Contributors state={state} setState={setState} />}
                    {step === 4 && <Step5Review state={state} />}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-white/[0.06] flex items-center justify-between shrink-0 bg-black/20">
                    <button
                        onClick={() => step === 0 ? onClose() : setStep(s => s - 1)}
                        className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        {step === 0 ? "Cancel" : "Back"}
                    </button>

                    <div className="flex items-center gap-2">
                        {step < 4 && (
                            <span className="text-xs text-white/20">Step {step + 1} of 5</span>
                        )}
                        {step < 4 ? (
                            <button
                                id="wizard-next-btn"
                                onClick={handleNext}
                                disabled={!canAdvance()}
                                className="flex items-center gap-2 bg-white text-black text-sm font-bold px-5 py-2 rounded-full hover:bg-white/90 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                                Continue <ChevronRight className="h-4 w-4" />
                            </button>
                        ) : (
                            <button
                                id="wizard-launch-btn"
                                onClick={handleLaunch}
                                disabled={isLaunching}
                                className="flex items-center gap-2 bg-white text-black text-sm font-bold px-5 py-2 rounded-full hover:bg-white/90 transition-colors disabled:opacity-60"
                            >
                                {isLaunching ? (
                                    <><Loader2 className="h-4 w-4 animate-spin" /> Launching...</>
                                ) : (
                                    <><Rocket className="h-4 w-4" /> Launch Project</>
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
