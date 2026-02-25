import React, { useState } from "react";
import { NewProjectWizard } from "@/src/components/NewProjectWizard";
import {
  LayoutDashboard,
  Settings,
  Search,
  Bell,
  Waves,
  Plus,
  Users,
  Clock,
  GitBranch,
  CheckCircle2,
  AlertCircle,
  CircleDot,
  Lock,
  X,
  ChevronRight,
  Upload,
  Zap,
} from "lucide-react";
import { cn } from "@/src/lib/utils";
import { Particles } from "@/src/components/ui/particles";

// ─── Types ───────────────────────────────────────────────────────────────────

type ComponentStatus = "stable" | "flagged" | "pending" | "locked";

interface Contributor {
  id: string;
  name: string;
  initials: string;
  color: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  owner: { name: string; initials: string; color: string };
  role: "Owner" | "Contributor";
  componentCount: number;
  contributorCount: number;
  lastActivity: string;
  activeChanges: number;
  status: ComponentStatus;
  isDraft?: boolean;
}

interface PendingInvite {
  id: string;
  projectName: string;
  owner: { name: string; initials: string; color: string };
  component: string;
  role: "contributor" | "read_only";
}

interface Notification {
  id: string;
  message: string;
  time: string;
  read: boolean;
  type: "change" | "invite" | "approved";
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_PROJECTS: Project[] = [
  {
    id: "1",
    name: "E-Commerce Platform",
    description: "Full-stack marketplace with microservices architecture",
    owner: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
    role: "Owner",
    componentCount: 8,
    contributorCount: 5,
    lastActivity: "2 hours ago",
    activeChanges: 2,
    status: "flagged",
  },
  {
    id: "2",
    name: "Auth Service",
    description: "Centralised authentication and authorisation system",
    owner: { name: "Priya Sharma", initials: "PS", color: "from-emerald-500 to-green-600" },
    role: "Contributor",
    componentCount: 4,
    contributorCount: 3,
    lastActivity: "5 hours ago",
    activeChanges: 1,
    status: "pending",
  },
  {
    id: "3",
    name: "Analytics Dashboard",
    description: "Real-time data visualisation and reporting pipeline",
    owner: { name: "Raj Patel", initials: "RP", color: "from-amber-500 to-orange-600" },
    role: "Contributor",
    componentCount: 6,
    contributorCount: 4,
    lastActivity: "Yesterday",
    activeChanges: 0,
    status: "stable",
  },
  {
    id: "4",
    name: "Mobile API Gateway",
    description: "REST gateway layer for iOS and Android clients",
    owner: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
    role: "Owner",
    componentCount: 5,
    contributorCount: 2,
    lastActivity: "3 days ago",
    activeChanges: 0,
    status: "stable",
  },
];

const MOCK_INVITES: PendingInvite[] = [
  {
    id: "inv1",
    projectName: "Billing Microservice",
    owner: { name: "Sarah Chen", initials: "SC", color: "from-rose-500 to-pink-600" },
    component: "Payment Processor",
    role: "contributor",
  },
];

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "n1",
    message: "Heads up — a change in Auth might affect your Dashboard code.",
    time: "10 min ago",
    read: false,
    type: "change",
  },
  {
    id: "n2",
    message: "validateUser signature update — impact mapped across 3 components.",
    time: "1 hour ago",
    read: false,
    type: "change",
  },
  {
    id: "n3",
    message: "Shipped cleanly ✓ — Mobile API Gateway change confirmed by all.",
    time: "3 hours ago",
    read: true,
    type: "approved",
  },
];

// ─── Status Helpers ───────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<ComponentStatus, { label: string; icon: React.ElementType; className: string; dotClass: string }> = {
  stable: { label: "Stable", icon: CheckCircle2, className: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20", dotClass: "bg-emerald-400" },
  flagged: { label: "Flagged", icon: AlertCircle, className: "text-orange-400 bg-orange-400/10 border-orange-400/20", dotClass: "bg-orange-400" },
  pending: { label: "Pending", icon: CircleDot, className: "text-yellow-400 bg-yellow-400/10 border-yellow-400/20", dotClass: "bg-yellow-400" },
  locked: { label: "Locked", icon: Lock, className: "text-white/40 bg-white/5 border-white/10", dotClass: "bg-white/40" },
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const Avatar = ({ initials, color, size = "sm" }: { initials: string; color: string; size?: "sm" | "md" | "lg" }) => {
  const sizeClass = { sm: "h-6 w-6 text-[10px]", md: "h-8 w-8 text-xs", lg: "h-10 w-10 text-sm" }[size];
  return (
    <div className={cn("rounded-full bg-gradient-to-br flex items-center justify-center font-bold text-white shrink-0", sizeClass, color)}>
      {initials}
    </div>
  );
};

const StatusBadge = ({ status }: { status: ComponentStatus }) => {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[11px] font-semibold px-2 py-0.5 rounded-full border", cfg.className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dotClass)} />
      {cfg.label}
    </span>
  );
};

const SkeletonCard = () => (
  <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 animate-pulse">
    <div className="flex justify-between items-start mb-4">
      <div className="h-4 w-32 bg-white/10 rounded-md" />
      <div className="h-5 w-16 bg-white/5 rounded-full" />
    </div>
    <div className="h-3 w-48 bg-white/5 rounded-md mb-6" />
    <div className="flex gap-4 mb-5">
      <div className="h-3 w-20 bg-white/5 rounded" />
      <div className="h-3 w-20 bg-white/5 rounded" />
    </div>
    <div className="flex justify-between items-center pt-4 border-t border-white/5">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => <div key={i} className="h-6 w-6 rounded-full bg-white/10" />)}
      </div>
      <div className="h-3 w-16 bg-white/5 rounded" />
    </div>
  </div>
);

const ProjectCard = ({ project, onClick }: { project: Project; onClick: () => void }) => (
  <div
    onClick={onClick}
    className="group relative bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.12] rounded-2xl p-5 cursor-pointer transition-all duration-300 overflow-hidden"
  >
    {/* Subtle glow on hover */}
    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
      <div className="absolute -top-16 -right-16 h-32 w-32 rounded-full bg-white/[0.03] blur-2xl" />
    </div>

    {project.isDraft && (
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-amber-500/0 via-amber-400 to-amber-500/0 rounded-t-2xl" />
    )}

    <div className="relative">
      {/* Header */}
      <div className="flex items-start justify-between mb-1.5">
        <h3 className="font-semibold text-white text-[15px] leading-tight group-hover:text-white transition-colors">
          {project.name}
        </h3>
        <StatusBadge status={project.status} />
      </div>

      <p className="text-white/40 text-xs leading-relaxed mb-4 line-clamp-2">{project.description}</p>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-white/40 text-xs mb-4">
        <span className="flex items-center gap-1.5">
          <GitBranch className="h-3 w-3" />
          {project.componentCount} components
        </span>
        <span className="flex items-center gap-1.5">
          <Users className="h-3 w-3" />
          {project.contributorCount} contributors
        </span>
        {project.activeChanges > 0 && (
          <span className="flex items-center gap-1.5 text-orange-400">
            <Zap className="h-3 w-3" />
            {project.activeChanges} active
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Avatar initials={project.owner.initials} color={project.owner.color} size="sm" />
          <span className="text-white/40 text-[11px]">
            <span className={cn("font-medium", project.role === "Owner" ? "text-violet-400" : "text-white/60")}>
              {project.role}
            </span>
          </span>
        </div>
        <span className="text-white/25 text-[11px] flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {project.lastActivity}
        </span>
      </div>
    </div>
  </div>
);

const EmptyState = ({ onUpload }: { onUpload: () => void }) => (
  <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
    <div className="relative mb-6">
      <div className="h-20 w-20 rounded-2xl bg-white/[0.03] border border-white/[0.08] flex items-center justify-center">
        <Waves className="h-8 w-8 text-white/20" />
      </div>
      <div className="absolute -bottom-1 -right-1 h-7 w-7 rounded-lg bg-white text-black flex items-center justify-center">
        <Plus className="h-4 w-4" />
      </div>
    </div>
    <h3 className="text-white font-semibold text-lg mb-2">You're all set</h3>
    <p className="text-white/40 text-sm max-w-xs leading-relaxed mb-6">
      Drop your files or paste a GitHub link and Ripple will show you how your code connects.
    </p>
    <button
      onClick={onUpload}
      className="flex items-center gap-2 bg-white text-black text-sm font-bold px-5 py-2.5 rounded-full hover:bg-white/90 transition-colors"
    >
      <Upload className="h-4 w-4" />
      Upload a Project
    </button>
  </div>
);

const InviteModal = ({
  invite,
  onAccept,
  onDecline,
  remaining,
}: {
  invite: PendingInvite;
  onAccept: () => void;
  onDecline: () => void;
  remaining: number;
}) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
    <div className="relative bg-zinc-950 border border-white/10 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
      {remaining > 1 && (
        <span className="absolute top-4 right-4 text-[10px] text-white/30 font-medium bg-white/5 px-2 py-0.5 rounded-full">
          +{remaining - 1} more
        </span>
      )}
      <div className="flex items-center gap-3 mb-5">
        <Avatar initials={invite.owner.initials} color={invite.owner.color} size="md" />
        <div>
          <p className="text-white text-sm font-semibold">{invite.owner.name}</p>
          <p className="text-white/40 text-xs">invited you to collaborate</p>
        </div>
      </div>

      <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-4 mb-5 space-y-2.5">
        <div className="flex justify-between text-xs">
          <span className="text-white/40">Project</span>
          <span className="text-white font-medium">{invite.projectName}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-white/40">Component</span>
          <span className="text-white font-medium">{invite.component}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-white/40">Role</span>
          <span className="text-white font-medium capitalize">{invite.role.replace("_", " ")}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={onDecline}
          className="flex-1 py-2 text-sm font-medium text-white/50 hover:text-white border border-white/10 hover:border-white/20 rounded-xl transition-colors"
        >
          Decline
        </button>
        <button
          onClick={onAccept}
          className="flex-1 py-2 text-sm font-bold text-black bg-white hover:bg-white/90 rounded-xl transition-colors"
        >
          Accept
        </button>
      </div>
    </div>
  </div>
);

const NotificationPanel = ({ notifications, onClose }: { notifications: Notification[]; onClose: () => void }) => (
  <div className="absolute right-0 top-12 z-50 w-80 bg-zinc-950 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
    <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
      <span className="text-sm font-semibold text-white">Notifications</span>
      <button onClick={onClose} className="text-white/40 hover:text-white transition-colors">
        <X className="h-4 w-4" />
      </button>
    </div>
    <div className="max-h-72 overflow-y-auto">
      {notifications.map((n) => (
        <div key={n.id} className={cn("px-4 py-3 border-b border-white/[0.04] last:border-0 hover:bg-white/[0.03] transition-colors", !n.read && "bg-white/[0.02]")}>
          <div className="flex gap-3">
            <span className={cn("mt-0.5 h-2 w-2 rounded-full shrink-0", !n.read ? "bg-violet-500" : "bg-transparent border border-white/20")} />
            <div>
              <p className="text-xs text-white/70 leading-relaxed">{n.message}</p>
              <p className="text-[10px] text-white/25 mt-1">{n.time}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
    <div className="px-4 py-3 border-t border-white/[0.06]">
      <button className="text-xs text-white/40 hover:text-white transition-colors flex items-center gap-1 mx-auto">
        View all <ChevronRight className="h-3 w-3" />
      </button>
    </div>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────

export const HomePage = ({
  onLogout,
  onProjectClick,
  onOpenProfile,
  onOpenView
}: {
  onLogout: () => void;
  onProjectClick: (projectId: string) => void;
  onOpenProfile?: () => void;
  onOpenView?: (viewType: 'global-changes' | 'global-teams' | 'global-notifications') => void;
}) => {
  const [isLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [invites, setInvites] = useState<PendingInvite[]>(MOCK_INVITES);
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);

  const handleProjectLaunch = (projectName: string) => {
    const newProject: Project = {
      id: `proj-${Date.now()}`,
      name: projectName,
      description: "Newly created project — dependency graph is being mapped.",
      owner: { name: "Alex Rivera", initials: "AR", color: "from-violet-500 to-purple-600" },
      role: "Owner",
      componentCount: 0,
      contributorCount: 1,
      lastActivity: "Just now",
      activeChanges: 0,
      status: "stable",
    };
    setProjects(prev => [newProject, ...prev]);
    setShowUploadModal(false);
  };

  const unreadCount = MOCK_NOTIFICATIONS.filter((n) => !n.read).length;
  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAcceptInvite = () => setInvites((prev) => prev.slice(1));
  const handleDeclineInvite = () => setInvites((prev) => prev.slice(1));

  const handleNavClick = (label: string) => {
    if (label === 'Changes') onOpenView?.('global-changes');
    else if (label === 'Teams') onOpenView?.('global-teams');
    else if (label === 'Notifications') onOpenView?.('global-notifications');
    // Dashboard is the current view, Settings is currently handled via project overview or future global settings
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden relative">
      {/* Particle background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <Particles quantity={120} className="absolute inset-0 h-full w-full" color="#ffffff" staticity={80} size={0.3} />
      </div>

      {/* Sidebar */}
      <aside className="relative z-10 w-60 border-r border-white/[0.06] flex flex-col px-3 py-5 shrink-0 bg-black/40 backdrop-blur-sm">
        <div className="flex items-center gap-2 px-2 mb-8">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-black">
            <Waves className="h-4 w-4" />
          </div>
          <span className="text-base font-bold tracking-tight">Ripple</span>
        </div>

        <nav className="flex-1 space-y-0.5">
          {[
            { icon: LayoutDashboard, label: "Dashboard", active: true },
            { icon: GitBranch, label: "Changes" },
            { icon: Users, label: "Teams" },
            { icon: Bell, label: "Notifications", badge: unreadCount },
            { icon: Settings, label: "Settings" },
          ].map(({ icon: Icon, label, active, badge }) => (
            <div
              key={label}
              onClick={() => handleNavClick(label)}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all group",
                active ? "bg-white/10 text-white" : "text-white/40 hover:bg-white/5 hover:text-white"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="text-sm font-medium flex-1">{label}</span>
              {badge ? (
                <span className="h-4 min-w-4 px-1 text-[10px] font-bold bg-violet-600 text-white rounded-full flex items-center justify-center">
                  {badge}
                </span>
              ) : null}
            </div>
          ))}
        </nav>

        <div className="pt-4 border-t border-white/[0.06]">
          <div className="px-2">
            <div
              onClick={() => onOpenProfile?.()}
              className="flex items-center gap-3 px-2 py-2 rounded-lg cursor-pointer hover:bg-white/5 transition-colors group mb-1"
            >
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-xs font-bold shrink-0">
                AR
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">Alex Rivera</p>
                <p className="text-[11px] text-white/30 truncate">alex@ripple.ai</p>
              </div>
              <ChevronRight className="h-3 w-3 text-white/20 group-hover:text-white/50 transition-colors" />
            </div>
            <button
              onClick={onLogout}
              className="w-full text-left text-[11px] text-white/25 hover:text-white/50 px-2 py-1 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>

      </aside>

      {/* Main */}
      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-14 border-b border-white/[0.06] flex items-center justify-between px-6 shrink-0 bg-black/20 backdrop-blur-sm">
          <div className="relative max-w-sm w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/20 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects or components..."
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-full py-1.5 pl-9 pr-4 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Bell */}
            <div className="relative">
              <button
                id="notifications-btn"
                onClick={() => setShowNotifications((v) => !v)}
                className="p-2 hover:bg-white/5 rounded-full transition-colors relative"
              >
                <Bell className="h-4 w-4 text-white/50" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-violet-500 rounded-full border border-black" />
                )}
              </button>
              {showNotifications && (
                <NotificationPanel
                  notifications={MOCK_NOTIFICATIONS}
                  onClose={() => setShowNotifications(false)}
                />
              )}
            </div>

            {/* New Project FAB */}
            <button
              id="new-project-btn"
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 bg-white text-black text-sm font-bold px-4 py-1.5 rounded-full hover:bg-white/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              New Project
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-6 py-8">

            {/* Page title */}
            <div className="flex items-end justify-between mb-6">
              <div>
                <h1 className="text-xl font-bold text-white">Your Projects</h1>
                <p className="text-white/30 text-sm mt-0.5">
                  {projects.length > 0
                    ? `${projects.length} project${projects.length > 1 ? "s" : ""} — click one to explore its components`
                    : "No projects yet"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {[
                  { label: "All", active: true },
                  { label: "Owner" },
                  { label: "Contributor" },
                ].map(({ label, active }) => (
                  <button
                    key={label}
                    className={cn(
                      "px-3 py-1 text-xs font-medium rounded-full border transition-colors",
                      active
                        ? "bg-white/10 border-white/20 text-white"
                        : "border-white/[0.06] text-white/30 hover:text-white hover:border-white/15"
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Project Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isLoading ? (
                [0, 1, 2, 3].map((i) => <SkeletonCard key={i} />)
              ) : filteredProjects.length === 0 && searchQuery === "" ? (
                <EmptyState onUpload={() => setShowUploadModal(true)} />
              ) : filteredProjects.length === 0 ? (
                <div className="col-span-full py-16 text-center">
                  <p className="text-white/30 text-sm">No projects matching "{searchQuery}"</p>
                </div>
              ) : (
                filteredProjects.map((p) => (
                  <ProjectCard key={p.id} project={p} onClick={() => onProjectClick(p.id)} />
                ))
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Invite Modal */}
      {invites.length > 0 && (
        <InviteModal
          invite={invites[0]}
          remaining={invites.length}
          onAccept={handleAcceptInvite}
          onDecline={handleDeclineInvite}
        />
      )}

      {/* Full 5-step New Project Wizard */}
      {showUploadModal && (
        <NewProjectWizard
          onClose={() => setShowUploadModal(false)}
          onLaunch={handleProjectLaunch}
        />
      )}
    </div>
  );
};
