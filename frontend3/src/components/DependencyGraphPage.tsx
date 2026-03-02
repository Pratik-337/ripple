import React, { useState, useCallback, useEffect, useMemo } from "react";
import ReactFlow, {
    Node, Edge, Background, Controls, MiniMap,
    useNodesState, useEdgesState, addEdge,
    MarkerType, Position, Handle, BackgroundVariant,
    useReactFlow, ReactFlowProvider,
    NodeProps, EdgeProps, getBezierPath,
} from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";
import {
    ArrowLeft, Waves, ZoomIn, ZoomOut, Maximize2, LayoutTemplate,
    GitBranch, Users, FileCode2, Clock, Zap, CheckCircle2,
    AlertCircle, CircleDot, Lock, X, ChevronRight, Network,
    RefreshCw, Eye, Shield
} from "lucide-react";
import { cn } from "@/src/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { componentsApi, changesApi } from "@/src/lib/api";

// ─── Types ─────────────────────────────────────────────────────────────────

type ComponentStatus = "stable" | "flagged" | "pending" | "locked";

interface Contributor { id: string; name: string; initials: string; color: string; }

interface ComponentNode {
    id: string;
    name: string;
    status: ComponentStatus;
    fileCount: number;
    contributors: Contributor[];
    lastActivity: string;
    activeChanges: number;
    isMyComponent: boolean;
}

interface Dependency {
    from: string;
    to: string;
    type: "import" | "calls" | "event";
    hasActiveChange: boolean;
    label?: string;
}

// ─── Mock Data ─────────────────────────────────────────────────────────────



// ─── Status Config ──────────────────────────────────────────────────────────

const STATUS_CFG = {
    stable: { label: "Stable", dot: "bg-emerald-400", ring: "border-emerald-400/20", glow: "", badge: "text-emerald-400 bg-emerald-400/10" },
    flagged: { label: "Flagged", dot: "bg-orange-400", ring: "border-orange-400/40", glow: "shadow-[0_0_16px_rgba(251,146,60,0.25)]", badge: "text-orange-400 bg-orange-400/10" },
    pending: { label: "Pending", dot: "bg-yellow-400", ring: "border-yellow-400/40", glow: "shadow-[0_0_16px_rgba(251,191,36,0.20)]", badge: "text-yellow-400 bg-yellow-400/10" },
    locked: { label: "Locked", dot: "bg-white/30", ring: "border-white/15", glow: "", badge: "text-white/40 bg-white/5" },
};

// ─── Dagre Layout ───────────────────────────────────────────────────────────

const nodeWidth = 220;
const nodeHeight = 130;

function getLayoutedElements(
    nodes: Node[],
    edges: Edge[],
    direction: "LR" | "TB" = "LR"
) {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: direction, nodesep: 60, ranksep: 100 });

    nodes.forEach((n) => dagreGraph.setNode(n.id, { width: nodeWidth, height: nodeHeight }));
    edges.forEach((e) => dagreGraph.setEdge(e.source, e.target));
    dagre.layout(dagreGraph);

    return {
        nodes: nodes.map((n) => {
            const pos = dagreGraph.node(n.id);
            return { ...n, position: { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 } };
        }),
        edges,
    };
}

// ─── Custom Animated Edge ───────────────────────────────────────────────────

const EDGE_COLORS = { import: "#8b5cf6", calls: "#3b82f6", event: "#10b981" };
const EDGE_LABELS: Record<string, string> = { import: "imports", calls: "calls", event: "event" };

function AnimatedChangeEdge({
    id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
    data, style = {}
}: EdgeProps) {
    const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
    const color = data?.color ?? "#ffffff33";
    const isActive = data?.hasActiveChange;
    const edgeLabel = data?.label;

    return (
        <>
            <path
                id={id}
                style={{ ...style, stroke: color, strokeWidth: isActive ? 2 : 1.5, opacity: isActive ? 0.85 : 0.35 }}
                className="react-flow__edge-path"
                d={edgePath}
            />
            {isActive && (
                <circle r="4" fill={color} opacity="0.9">
                    <animateMotion dur="1.8s" repeatCount="indefinite" path={edgePath} />
                </circle>
            )}
            {edgeLabel && (
                <foreignObject width="80" height="18" x={labelX - 40} y={labelY - 9} style={{ overflow: "visible", pointerEvents: "none" }}>
                    <div className="flex items-center justify-center">
                        <div className={cn(
                            "text-[9px] font-mono px-1.5 py-0.5 rounded-full whitespace-nowrap",
                            isActive ? "bg-orange-400/20 text-orange-300/90 border border-orange-400/30" : "bg-black/60 text-white/30 border border-white/10"
                        )}>
                            {edgeLabel}
                        </div>
                    </div>
                </foreignObject>
            )}
        </>
    );
}

// ─── Custom Component Node ──────────────────────────────────────────────────

function ComponentGraphNode({ data, selected }: NodeProps) {
    const cfg = STATUS_CFG[data.status as ComponentStatus];
    const maxAvatars = 3;

    return (
        <div className={cn(
            "relative bg-zinc-950 border rounded-2xl px-4 py-3.5 transition-all duration-200 cursor-pointer select-none",
            "w-[220px]",
            cfg.ring,
            cfg.glow,
            selected ? "border-violet-400/60 shadow-[0_0_20px_rgba(139,92,246,0.3)] scale-105" : "hover:border-white/20 hover:shadow-[0_0_12px_rgba(255,255,255,0.08)]",
            data.status === "locked" ? "opacity-70" : ""
        )}>
            {/* Active change pulse ring */}
            {data.activeChanges > 0 && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-60" />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-orange-500" />
                </span>
            )}

            <Handle type="target" position={Position.Left} style={{ background: "transparent", border: "none" }} />
            <Handle type="source" position={Position.Right} style={{ background: "transparent", border: "none" }} />

            <div className="flex items-center gap-1.5 mb-1.5">
                <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", cfg.dot)} />
                <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-full", cfg.badge)}>
                    {cfg.label}
                </span>
                {data.activeChanges > 0 && (
                    <span className="text-[9px] text-orange-400/80 bg-orange-400/10 px-1 py-0.5 rounded-full ml-auto">
                        {data.activeChanges} active
                    </span>
                )}
            </div>

            <p className="text-[13px] font-bold text-white leading-tight mb-2">{data.name}</p>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[10px] text-white/30">
                    <span className="flex items-center gap-0.5"><FileCode2 className="h-2.5 w-2.5" />{data.fileCount}</span>
                    <span className="flex items-center gap-0.5"><Clock className="h-2.5 w-2.5" />{data.lastActivity}</span>
                </div>
                <div className="flex items-center">
                    {data.contributors.slice(0, maxAvatars).map((c: Contributor, i: number) => (
                        <div
                            key={c.id}
                            style={{ marginLeft: i === 0 ? 0 : -5, zIndex: maxAvatars - i }}
                            className={cn("h-5 w-5 rounded-full bg-gradient-to-br flex items-center justify-center text-[8px] font-bold text-white relative border border-zinc-950", c.color)}
                        >
                            {c.initials}
                        </div>
                    ))}
                    {data.contributors.length > maxAvatars && (
                        <div className="h-5 w-5 rounded-full bg-white/10 flex items-center justify-center text-[8px] text-white/50 border border-zinc-950 relative" style={{ marginLeft: -5, zIndex: 0 }}>
                            +{data.contributors.length - maxAvatars}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

const nodeTypes = { component: ComponentGraphNode };
const edgeTypes = { animated: AnimatedChangeEdge };

// ─── Detail Panel ───────────────────────────────────────────────────────────

const DetailPanel = ({
    component,
    dependencies,
    components,
    onClose,
    onOpenIDE,
}: {
    component: ComponentNode;
    dependencies: Dependency[];
    components: ComponentNode[];
    onClose: () => void;
    onOpenIDE: () => void;
}) => {
    const cfg = STATUS_CFG[component.status];
    const incoming = dependencies.filter(d => d.to === component.id);
    const outgoing = dependencies.filter(d => d.from === component.id);

    return (
        <aside className="absolute right-4 top-4 bottom-4 w-72 bg-zinc-950/95 backdrop-blur-md border border-white/10 rounded-2xl flex flex-col shadow-2xl z-10 overflow-hidden">
            {/* Header */}
            <div className="flex items-start justify-between px-4 py-3.5 border-b border-white/[0.06]">
                <div>
                    <div className="flex items-center gap-1.5 mb-1">
                        <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
                        <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-full", cfg.badge)}>{cfg.label}</span>
                    </div>
                    <h3 className="text-[14px] font-bold text-white">{component.name}</h3>
                    <p className="text-[11px] text-white/35 mt-0.5">{component.fileCount} files · {component.lastActivity}</p>
                </div>
                <button onClick={onClose} className="text-white/25 hover:text-white transition-colors mt-0.5">
                    <X className="h-4 w-4" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {/* Contributors */}
                <div className="px-4 py-3 border-b border-white/[0.04]">
                    <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Contributors</p>
                    <div className="space-y-1.5">
                        {component.contributors.map(c => (
                            <div key={c.id} className="flex items-center gap-2">
                                <div className={cn("h-5 w-5 rounded-full bg-gradient-to-br flex items-center justify-center text-[8px] font-bold text-white shrink-0", c.color)}>
                                    {c.initials}
                                </div>
                                <span className="text-xs text-white/60">{c.name}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Active changes */}
                {component.activeChanges > 0 && (
                    <div className="px-4 py-3 border-b border-white/[0.04]">
                        <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-orange-400 animate-pulse" />
                            <p className="text-xs text-orange-400 font-medium">{component.activeChanges} active change{component.activeChanges > 1 ? "s" : ""} propagating</p>
                        </div>
                    </div>
                )}

                {/* Edges — upstream */}
                {incoming.length > 0 && (
                    <div className="px-4 py-3 border-b border-white/[0.04]">
                        <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Depends on</p>
                        <div className="space-y-1.5">
                            {incoming.map((dep, i) => {
                                const src = components.find(c => c.id === dep.from);
                                return src ? (
                                    <div key={i} className="flex items-center gap-2">
                                        <div className={cn("h-2 w-2 rounded-full shrink-0", STATUS_CFG[src.status].dot)} />
                                        <span className="text-xs text-white/60 flex-1">{src.name}</span>
                                        <span className="text-[9px] font-mono text-white/25 bg-white/5 px-1.5 rounded">{dep.label}</span>
                                        {dep.hasActiveChange && <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />}
                                    </div>
                                ) : null;
                            })}
                        </div>
                    </div>
                )}

                {/* Edges — downstream */}
                {outgoing.length > 0 && (
                    <div className="px-4 py-3 border-b border-white/[0.04]">
                        <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Used by</p>
                        <div className="space-y-1.5">
                            {outgoing.map((dep, i) => {
                                const tgt = components.find(c => c.id === dep.to);
                                return tgt ? (
                                    <div key={i} className="flex items-center gap-2">
                                        <div className={cn("h-2 w-2 rounded-full shrink-0", STATUS_CFG[tgt.status].dot)} />
                                        <span className="text-xs text-white/60 flex-1">{tgt.name}</span>
                                        <span className="text-[9px] font-mono text-white/25 bg-white/5 px-1.5 rounded">{dep.label}</span>
                                        {dep.hasActiveChange && <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />}
                                    </div>
                                ) : null;
                            })}
                        </div>
                    </div>
                )}
            </div>

            <div className="px-4 py-3 border-t border-white/[0.06]">
                <button
                    id={`graph-open-ide-${component.id}`}
                    onClick={onOpenIDE}
                    className="w-full py-2 text-xs font-bold text-black bg-white hover:bg-white/90 rounded-xl transition-colors"
                >
                    Open in IDE
                </button>
            </div>
        </aside>
    );
};

// ─── Legend ─────────────────────────────────────────────────────────────────

const Legend = () => (
    <div className="absolute left-4 bottom-4 bg-zinc-950/90 backdrop-blur-sm border border-white/10 rounded-xl px-4 py-3 z-10 space-y-2.5">
        <p className="text-[9px] font-semibold text-white/30 uppercase tracking-wider">Legend</p>
        <div className="space-y-1.5">
            {[
                { color: "bg-emerald-400", label: "Stable" },
                { color: "bg-orange-400", label: "Flagged — active change" },
                { color: "bg-yellow-400", label: "Pending review" },
                { color: "bg-white/30", label: "Locked" },
            ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-2">
                    <span className={cn("h-2 w-2 rounded-full shrink-0", color)} />
                    <span className="text-[10px] text-white/40">{label}</span>
                </div>
            ))}
        </div>
        <div className="pt-1 border-t border-white/[0.06] space-y-1.5">
            {[
                { color: "bg-violet-500", label: "import", animated: false },
                { color: "bg-blue-500", label: "calls", animated: false },
                { color: "bg-emerald-500", label: "event", animated: false },
                { color: "bg-orange-400", label: "active propagation", animated: true },
            ].map(({ color, label, animated }) => (
                <div key={label} className="flex items-center gap-2">
                    <div className="relative h-0.5 w-6 bg-white/10 rounded-full overflow-hidden">
                        <div className={cn("h-full rounded-full", color, animated ? "w-3" : "w-6")} />
                    </div>
                    <span className="text-[10px] text-white/40">{label}</span>
                </div>
            ))}
        </div>
    </div>
);

// ─── Inner Graph (needs ReactFlowProvider) ──────────────────────────────────

interface InnerGraphProps {
    components: ComponentNode[];
    dependencies: Dependency[];
    onNodeClick: (c: ComponentNode | null) => void;
    selectedId: string | null;
    direction: "LR" | "TB";
}

function buildNodesAndEdges(components: ComponentNode[], dependencies: Dependency[], selectedId: string | null, direction: "LR" | "TB") {
    const rawNodes: Node[] = components.map(c => ({
        id: c.id,
        type: "component",
        position: { x: 0, y: 0 },
        data: { ...c },
        selected: c.id === selectedId,
    }));

    const rawEdges: Edge[] = dependencies.map((dep, i) => {
        const color = dep.hasActiveChange ? "#fb923c" : { import: "#8b5cf680", calls: "#3b82f680", event: "#10b98180" }[dep.type];
        return {
            id: `e${i}`,
            source: dep.from,
            target: dep.to,
            type: "animated",
            markerEnd: { type: MarkerType.ArrowClosed, color, width: 12, height: 12 },
            data: { hasActiveChange: dep.hasActiveChange, color, label: dep.label, type: dep.type },
        };
    });

    return getLayoutedElements(rawNodes, rawEdges, direction);
}

function InnerGraph({ components, dependencies, onNodeClick, selectedId, direction }: InnerGraphProps) {
    const { nodes: ln, edges: le } = useMemo(() => buildNodesAndEdges(components, dependencies, selectedId, direction), [components, dependencies, selectedId, direction]);
    const [nodes, setNodes, onNodesChange] = useNodesState(ln);
    const [edges, setEdges, onEdgesChange] = useEdgesState(le);
    const { fitView } = useReactFlow();

    useEffect(() => {
        setNodes(ln);
        setEdges(le);
        setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 50);
    }, [ln, le, fitView]);

    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        const comp = components.find(c => c.id === node.id) ?? null;
        onNodeClick(comp);
    }, [onNodeClick]);

    const handlePaneClick = useCallback(() => {
        onNodeClick(null);
    }, [onNodeClick]);

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            minZoom={0.3}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
        >
            <Background
                variant={BackgroundVariant.Dots}
                gap={24}
                size={1}
                color="#ffffff08"
            />
            <Controls
                className="!bg-zinc-950 !border-white/10 !rounded-xl overflow-hidden !shadow-xl"
                style={{ bottom: 80, right: 16, top: "auto", left: "auto" }}
                showInteractive={false}
            />
            <MiniMap
                nodeColor={(n) => {
                    const comp = components.find(c => c.id === n.id);
                    if (!comp) return "#1a1a1a";
                    return { stable: "#10b981", flagged: "#f97316", pending: "#facc15", locked: "#ffffff30" }[comp.status] ?? "#333";
                }}
                maskColor="#00000090"
                style={{
                    backgroundColor: "#09090b",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 12,
                    bottom: 16,
                    right: 16,
                    top: "auto",
                    left: "auto",
                }}
                className="!right-4 !bottom-4"
            />
        </ReactFlow>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

interface DependencyGraphPageProps {
    projectId: string;
    onBack: () => void;
    onOpenIDE: (projectId: string, componentId: string, componentName: string, readOnly: boolean) => void;
}

export const DependencyGraphPage = ({ projectId, onBack, onOpenIDE }: DependencyGraphPageProps) => {
    const [selected, setSelected] = useState<ComponentNode | null>(null);
    const [direction, setDirection] = useState<"LR" | "TB">("LR");

    const changeId = new URLSearchParams(window.location.search).get('change_id');
    const { data: impactsData } = useQuery({
        queryKey: ['impact', changeId],
        queryFn: () => changesApi.getImpact(changeId!),
        enabled: !!changeId
    });

    const { data: components = [], isLoading: componentsLoading } = useQuery({
        queryKey: ['project', projectId, 'components'],
        queryFn: async () => {
            const comps = await componentsApi.list(projectId);
            const nodes: ComponentNode[] = comps.map(c => ({
                id: c.id,
                name: c.name,
                status: c.status as ComponentStatus,
                fileCount: 0,
                contributors: c.contributors.map(ct => ({
                    id: ct.user_id,
                    name: "Unknown",
                    initials: "??",
                    color: "from-gray-500 to-gray-600"
                })),
                lastActivity: "Unknown",
                activeChanges: 0,
                isMyComponent: false
            }));
            return nodes;
        }
    });

    const { data: dependencies = [], isLoading: depsLoading } = useQuery({
        queryKey: ['project', projectId, 'dependencies'],
        queryFn: async () => {
            if (!components.length) return [];
            const depsResponses = await Promise.all(components.map(c => componentsApi.getDependencies(c.id)));
            const edges: Dependency[] = [];
            const impactedComponentIds = impactsData ? new Set(impactsData.impacts.map(i => i.component_id)) : new Set<string>();

            depsResponses.forEach((res, i) => {
                const sourceId = components[i].id;
                res.depends_on.forEach(dep => {
                    const hasActiveChange = impactedComponentIds.has(sourceId) || impactedComponentIds.has(dep.target_component_id);
                    edges.push({
                        from: sourceId,
                        to: dep.target_component_id,
                        type: dep.dependency_type as "import" | "calls" | "event",
                        hasActiveChange,
                        label: dep.dependency_type
                    });
                });
            });
            return edges;
        },
        enabled: components.length > 0
    });

    const totalEdges = dependencies.length;
    const activeEdges = dependencies.filter(d => d.hasActiveChange).length;

    if (componentsLoading) {
        return <div className="flex h-screen items-center justify-center bg-[#08080a] text-white">Loading graph...</div>;
    }

    return (
        <div className="flex h-screen bg-[#08080a] text-white overflow-hidden flex-col">

            {/* ── Header ─────────────────────────────────────────────────────── */}
            <header className="shrink-0 flex items-center justify-between px-5 py-3 border-b border-white/[0.06] bg-black/50 backdrop-blur-sm z-20">
                <div className="flex items-center gap-3">
                    <div className="h-6 w-6 rounded-md bg-white flex items-center justify-center">
                        <Waves className="h-3.5 w-3.5 text-black" />
                    </div>
                    <button
                        id="graph-back-btn"
                        onClick={onBack}
                        className="flex items-center gap-1.5 text-white/40 hover:text-white transition-colors text-sm"
                    >
                        <ArrowLeft className="h-3.5 w-3.5" />
                        Project
                    </button>
                    <span className="text-white/20">/</span>
                    <div className="flex items-center gap-2">
                        <Network className="h-4 w-4 text-violet-400" />
                        <span className="text-sm font-semibold text-white">Dependency Graph</span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Stats */}
                    <div className="flex items-center gap-3 text-[11px] text-white/35">
                        <span>{components.length} components</span>
                        <span className="text-white/15">·</span>
                        <span>{totalEdges} connections</span>
                        {activeEdges > 0 && (
                            <>
                                <span className="text-white/15">·</span>
                                <span className="text-orange-400/80 flex items-center gap-1">
                                    <span className="h-1.5 w-1.5 rounded-full bg-orange-400 animate-pulse" />
                                    {activeEdges} active propagation{activeEdges > 1 ? "s" : ""}
                                </span>
                            </>
                        )}
                    </div>

                    {/* Layout direction toggle */}
                    <div className="flex items-center gap-1 bg-white/[0.04] border border-white/[0.08] rounded-xl p-1">
                        {(["LR", "TB"] as const).map(d => (
                            <button
                                key={d}
                                id={`layout-${d}`}
                                onClick={() => setDirection(d)}
                                className={cn(
                                    "flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-lg transition-colors",
                                    direction === d ? "bg-white/15 text-white" : "text-white/35 hover:text-white/60"
                                )}
                            >
                                <LayoutTemplate className={cn("h-3 w-3", d === "TB" && "rotate-90")} />
                                {d === "LR" ? "Left → Right" : "Top → Bottom"}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            {/* ── Graph canvas ───────────────────────────────────────────────── */}
            <div className="flex-1 relative">
                <ReactFlowProvider>
                    <InnerGraph
                        components={components}
                        dependencies={dependencies}
                        onNodeClick={setSelected}
                        selectedId={selected?.id ?? null}
                        direction={direction}
                    />
                </ReactFlowProvider>

                {/* Legend */}
                <Legend />

                {/* Floating active-change alert */}
                {activeEdges > 0 && (
                    <div className="absolute top-4 left-4 flex items-center gap-2 bg-orange-500/10 border border-orange-500/20 backdrop-blur-sm rounded-xl px-3 py-2 z-10 shadow-lg">
                        <Zap className="h-3.5 w-3.5 text-orange-400" />
                        <span className="text-xs text-orange-400">
                            <span className="font-bold">Authentication</span> change is propagating — {activeEdges} component{activeEdges > 1 ? "s" : ""} notified
                        </span>
                    </div>
                )}

                {/* Detail panel */}
                {selected && (
                    <DetailPanel
                        component={selected}
                        components={components}
                        dependencies={dependencies}
                        onClose={() => setSelected(null)}
                        onOpenIDE={() => onOpenIDE(projectId, selected.id, selected.name, !selected.isMyComponent)}
                    />
                )}
            </div>
        </div>
    );
};
