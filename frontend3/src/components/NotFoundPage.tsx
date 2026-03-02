import React from "react";
import { Waves, ArrowLeft, Home, RefreshCw } from "lucide-react";
import { Particles } from "@/src/components/ui/particles";
import { cn } from "@/src/lib/utils";

interface NotFoundPageProps {
    onGoHome: () => void;
    onGoToDashboard: () => void;
}

export const NotFoundPage = ({ onGoHome, onGoToDashboard }: NotFoundPageProps) => {
    return (
        <div className="flex h-screen bg-black text-white items-center justify-center overflow-hidden relative">
            {/* Particles */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <Particles
                    quantity={120}
                    className="absolute inset-0 h-full w-full"
                    color="#ffffff"
                    staticity={70}
                    size={0.3}
                />
            </div>

            <div className="relative z-10 flex flex-col items-center text-center px-6 select-none">
                {/* Logo */}
                <div className="flex items-center gap-2 mb-16">
                    <div className="h-7 w-7 rounded-lg bg-white flex items-center justify-center">
                        <Waves className="h-4 w-4 text-black" />
                    </div>
                    <span className="text-base font-bold text-white tracking-tight">Ripple</span>
                </div>

                {/* 404 */}
                <div className="relative mb-8">
                    <p
                        className="text-[160px] font-black leading-none select-none"
                        style={{
                            background: "linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.1) 100%)",
                            WebkitBackgroundClip: "text",
                            WebkitTextFillColor: "transparent",
                            backgroundClip: "text",
                            letterSpacing: "-8px",
                        }}
                    >
                        404
                    </p>
                    {/* Glow under the number */}
                    <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-violet-500/10 to-transparent blur-xl pointer-events-none" />
                </div>

                <h1 className="text-xl font-bold text-white mb-3">Page not found</h1>
                <p className="text-sm text-white/40 max-w-sm leading-relaxed mb-10">
                    This page has drifted out of range — it's not part of the current ripple. Check the URL or head somewhere safe.
                </p>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    <button
                        id="404-go-home-btn"
                        onClick={onGoHome}
                        className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white/50 hover:text-white border border-white/[0.08] hover:border-white/25 rounded-xl transition-colors"
                    >
                        <Home className="h-4 w-4" />
                        Go home
                    </button>
                    <button
                        id="404-go-dashboard-btn"
                        onClick={onGoToDashboard}
                        className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-black bg-white hover:bg-white/90 rounded-xl transition-colors shadow-[0_0_20px_rgba(255,255,255,0.15)]"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Dashboard
                    </button>
                </div>

                {/* Subtle footer */}
                <p className="mt-16 text-[11px] text-white/15">
                    If you think this is a mistake, the owner may need to re-share the link.
                </p>
            </div>
        </div>
    );
};
