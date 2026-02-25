import React, { useState } from "react";
import { Bell, Check, GitBranch, ShieldAlert, CheckCircle2, Waves, ArrowLeft } from "lucide-react";
import { cn } from "@/src/lib/utils";
import { Particles } from "./ui/particles";

type NotificationType = "change" | "approved" | "alert" | "invite";

interface Notification {
    id: string;
    message: string;
    time: string;
    read: boolean;
    type: NotificationType;
    project?: string;
    author?: string;
    avatarColor?: string;
    initials?: string;
}

const MOCK_NOTIFICATIONS: Notification[] = [
    {
        id: "n1",
        message: "Heads up — a change in Auth might affect your Dashboard code. \"Priya updated validateUser — 2 lines affected\"",
        time: "2 min ago",
        read: false,
        type: "alert",
        project: "Auth Service",
        author: "Priya Sharma",
        avatarColor: "from-emerald-500 to-green-600",
        initials: "PS",
    },
    {
        id: "n2",
        message: "validateUser signature update — impact mapped across 3 components.",
        time: "1 hour ago",
        read: false,
        type: "change",
        project: "Billing Microservice",
        author: "Raj Patel",
        avatarColor: "from-amber-500 to-orange-600",
        initials: "RP",
    },
    {
        id: "n3",
        message: "Shipped cleanly ✓ — validateUser update merged by the owner.",
        time: "3 hours ago",
        read: true,
        type: "approved",
        project: "Billing Microservice",
        author: "Alex Rivera",
        avatarColor: "from-violet-500 to-purple-600",
        initials: "AR",
    },
    {
        id: "n4",
        message: "Raj invited you to join Payments API as a contributor.",
        time: "Yesterday",
        read: true,
        type: "invite",
        project: "Payments API",
        author: "Raj Patel",
        avatarColor: "from-amber-500 to-orange-600",
        initials: "RP",
    }
];

const ICONS: Record<NotificationType, React.ElementType> = {
    change: GitBranch,
    approved: CheckCircle2,
    alert: ShieldAlert,
    invite: Waves,
};

const ICON_COLORS: Record<NotificationType, string> = {
    change: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    approved: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    alert: "text-orange-400 bg-orange-400/10 border-orange-400/20",
    invite: "text-violet-400 bg-violet-400/10 border-violet-400/20",
};

export const GlobalNotificationsPage = ({ onBack }: { onBack: () => void }) => {
    const [filter, setFilter] = useState<"all" | "unread" | "alerts" | "changes" | "invites">("all");
    const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);

    const filteredNotifications = notifications.filter(n => {
        if (filter === "unread") return !n.read;
        if (filter === "alerts") return n.type === "alert";
        if (filter === "changes") return n.type === "change" || n.type === "approved";
        if (filter === "invites") return n.type === "invite";
        return true;
    });

    const markAllRead = () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    };

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
                                <Bell className="h-4 w-4 text-white" />
                            </div>
                            <h1 className="text-lg font-bold">Notifications</h1>
                        </div>
                    </div>
                    <button
                        onClick={markAllRead}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs font-medium transition-colors"
                    >
                        <Check className="h-4 w-4" /> Mark all read
                    </button>
                </header>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 md:p-10">
                    <div className="max-w-4xl mx-auto">
                        {/* Filters */}
                        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2 scrollbar-hide">
                            {[
                                { id: "all", label: "All" },
                                { id: "unread", label: "Unread" },
                                { id: "alerts", label: "Impact Alerts" },
                                { id: "changes", label: "Changes" },
                                { id: "invites", label: "Invites" },
                            ].map(f => (
                                <button
                                    key={f.id}
                                    onClick={() => setFilter(f.id as any)}
                                    className={cn(
                                        "px-4 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap",
                                        filter === f.id
                                            ? "bg-white text-black"
                                            : "bg-white/5 text-white/50 hover:bg-white/10 hover:text-white"
                                    )}
                                >
                                    {f.label}
                                </button>
                            ))}
                        </div>

                        {/* Notification List */}
                        <div className="space-y-3">
                            {filteredNotifications.length > 0 ? (
                                filteredNotifications.map(notification => {
                                    const Icon = ICONS[notification.type];
                                    return (
                                        <div
                                            key={notification.id}
                                            className={cn(
                                                "group flex gap-4 p-5 rounded-2xl border transition-all duration-300",
                                                notification.read
                                                    ? "bg-white/[0.02] border-white/[0.04] hover:bg-white/[0.04]"
                                                    : "bg-white/[0.05] border-white/[0.10] hover:bg-white/[0.08]"
                                            )}
                                        >
                                            {/* Avatar / Icon */}
                                            <div className="relative shrink-0">
                                                <div className={cn("h-10 w-10 rounded-full bg-gradient-to-br flex items-center justify-center text-xs font-bold text-white", notification.avatarColor)}>
                                                    {notification.initials}
                                                </div>
                                                <div className={cn("absolute -bottom-1 -right-1 h-5 w-5 rounded-full flex items-center justify-center border-2 border-zinc-950", ICON_COLORS[notification.type])}>
                                                    <Icon className="h-2.5 w-2.5" />
                                                </div>
                                            </div>

                                            {/* Content */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-4 mb-1">
                                                    <p className={cn("text-[15px] leading-snug", notification.read ? "text-white/70" : "text-white font-medium")}>
                                                        {notification.message}
                                                    </p>
                                                    <span className="text-xs text-white/30 whitespace-nowrap shrink-0">{notification.time}</span>
                                                </div>
                                                <div className="flex flex-wrap items-center gap-3 mt-2 text-xs">
                                                    {notification.project && (
                                                        <span className="text-white/40 font-medium">{notification.project}</span>
                                                    )}
                                                    <div className="h-1 w-1 rounded-full bg-white/20" />
                                                    <button className="text-violet-400 hover:text-violet-300 font-medium transition-colors flex items-center gap-1">
                                                        {notification.type === "invite" ? "Accept Invite" : notification.type === "alert" ? "Review Impact" : "View Details"} &rarr;
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Unread dot */}
                                            {!notification.read && (
                                                <div className="shrink-0 flex items-center justify-center items-start pt-1.5">
                                                    <div className="h-2.5 w-2.5 bg-violet-500 rounded-full shadow-[0_0_10px_rgba(139,92,246,0.5)]" />
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="text-center py-20 border border-white/5 rounded-2xl bg-white/[0.02]">
                                    <Bell className="h-8 w-8 text-white/10 mx-auto mb-3" />
                                    <p className="text-white/40">No notifications found.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};
