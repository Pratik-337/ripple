import React, { useState } from "react";
import { Waves, RotateCcw, ArrowLeft, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import { Particles } from "@/src/components/ui/particles";

interface ErrorPageProps {
    error: Error | null;
    onRetry: () => void;
    onGoHome: () => void;
}

export const ErrorPage = ({ error, onRetry, onGoHome }: ErrorPageProps) => {
    const [showDetails, setShowDetails] = useState(false);

    return (
        <div className="flex h-screen bg-black text-white items-center justify-center overflow-hidden relative">
            <div className="fixed inset-0 z-0 pointer-events-none">
                <Particles
                    quantity={80}
                    className="absolute inset-0 h-full w-full"
                    color="#ffffff"
                    staticity={90}
                    size={0.2}
                />
            </div>

            <div className="relative z-10 flex flex-col items-center text-center px-6 max-w-md w-full">
                {/* Logo */}
                <div className="flex items-center gap-2 mb-14">
                    <div className="h-7 w-7 rounded-lg bg-white flex items-center justify-center">
                        <Waves className="h-4 w-4 text-black" />
                    </div>
                    <span className="text-base font-bold text-white tracking-tight">Ripple</span>
                </div>

                {/* Icon */}
                <div className="h-16 w-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mb-6">
                    <AlertTriangle className="h-8 w-8 text-rose-400" />
                </div>

                <h1 className="text-xl font-bold text-white mb-3">Something went wrong</h1>
                <p className="text-sm text-white/40 max-w-sm leading-relaxed mb-8">
                    An unexpected error occurred. Your work has been auto-saved. Try refreshing — if it keeps happening, let us know.
                </p>

                {/* Error details toggle */}
                {error && (
                    <div className="w-full mb-8">
                        <button
                            onClick={() => setShowDetails(v => !v)}
                            className="flex items-center gap-2 text-xs text-white/25 hover:text-white/50 transition-colors mx-auto mb-2"
                        >
                            {showDetails ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                            {showDetails ? "Hide" : "Show"} error details
                        </button>
                        {showDetails && (
                            <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-left font-mono text-[11px] text-rose-300/60 leading-relaxed max-h-40 overflow-y-auto">
                                <p className="text-white/50 mb-1">{error.name}</p>
                                <p>{error.message}</p>
                                {error.stack && (
                                    <pre className="mt-2 text-white/20 whitespace-pre-wrap text-[10px]">
                                        {error.stack.split("\n").slice(1, 6).join("\n")}
                                    </pre>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-3">
                    <button
                        id="error-go-home-btn"
                        onClick={onGoHome}
                        className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white/50 hover:text-white border border-white/[0.08] hover:border-white/25 rounded-xl transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Go home
                    </button>
                    <button
                        id="error-retry-btn"
                        onClick={onRetry}
                        className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-black bg-white hover:bg-white/90 rounded-xl transition-colors"
                    >
                        <RotateCcw className="h-4 w-4" />
                        Try again
                    </button>
                </div>
            </div>
        </div>
    );
};
