import React, { useState, useEffect } from "react";
import { Waves, ArrowRight } from "lucide-react";
import { GlowingEffect } from "./glowing-effect";

interface Web3HeroAnimatedProps {
  onSignIn?: () => void;
}

export function Web3HeroAnimated({ onSignIn }: Web3HeroAnimatedProps) {
  // Symmetric pillar heights (percent). Tall at edges, low at center.
  const pillars = [92, 84, 78, 70, 62, 54, 46, 34, 18, 34, 46, 54, 62, 70, 78, 84, 92];

  // State to trigger animations once the component is mounted.
  const [isMounted, setIsMounted] = useState(false);
  const [showHeader, setShowHeader] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsMounted(true), 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      setIsScrolled(currentScrollY > 20);

      // More sensitive: react immediately to scroll direction change after a tiny threshold
      if (currentScrollY > lastScrollY && currentScrollY > 20) {
        setShowHeader(false);
      } else {
        setShowHeader(true);
      }

      setLastScrollY(currentScrollY);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [lastScrollY]);

  return (
    <>
      <style>
        {`
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          @keyframes subtlePulse {
            0%, 100% {
              opacity: 0.8;
              transform: scale(1);
            }
            50% {
              opacity: 1;
              transform: scale(1.03);
            }
          }
          
          .animate-fadeInUp {
            animation: fadeInUp 0.8s ease-out forwards;
          }
        `}
      </style>

      <section className="relative isolate min-h-[80vh] overflow-hidden bg-transparent text-white font-sans">
        {/* ================== BACKGROUND ================== */}

        {/* ================== NAV ================== */}
        <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${showHeader ? 'translate-y-0' : '-translate-y-full'} ${isScrolled ? 'bg-black' : 'bg-transparent'}`}>
          <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-7 md:px-8">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white text-black">
                <Waves className="h-8 w-8" />
              </div>
              <span className="text-3xl font-bold tracking-tight">Ripple</span>
            </div>

            <nav className="hidden items-center gap-8 text-base font-medium text-white/70 md:flex">
              {['Product', 'Impact', 'Teams', 'Resources', 'Pricing'].map((i) => (
                <a key={i} className="transition hover:text-white" href="#">{i}</a>
              ))}
            </nav>

            <div className="hidden items-center gap-4 md:flex">
              <button
                onClick={onSignIn}
                className="text-medium font-medium text-white/70 transition hover:text-white"
              >
                Sign in
              </button>
              <button className="group flex items-center gap-2 rounded-full bg-white px-6 py-3 text-base font-semibold text-black shadow-lg transition hover:bg-white/90">
                Request Demo
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5" />
              </button>
            </div>

            <button className="md:hidden rounded-full bg-white/10 px-4 py-2 text-sm font-medium backdrop-blur-sm">Menu</button>
          </div>
        </header>

        {/* ================== COPY ================== */}
        <div className="relative z-10 mx-auto grid w-full max-w-5xl place-items-center px-6 pt-42 pb-20 md:pt-60 md:pb-32">
          <div className={`mx-auto text-center ${isMounted ? 'animate-fadeInUp' : 'opacity-0'}`}>
            <h1 style={{ animationDelay: '200ms' }} className={`mt-8 text-5xl font-light tracking-tight md:text-7xl lg:text-8xl ${isMounted ? 'animate-fadeInUp' : 'opacity-0'}`}>
              Orchestrate change <br className="hidden md:block" />
              <span className="bg-gradient-to-r from-white via-white to-white/40 bg-clip-text text-transparent">across your codebase</span>
            </h1>
            <p style={{ animationDelay: '300ms' }} className={`mx-auto mt-8 max-w-2xl text-balance text-lg text-white/70 md:text-xl ${isMounted ? 'animate-fadeInUp' : 'opacity-0'}`}>
              Automatically identify affected components, notify contributors, and streamline reviews for large-scale engineering teams.
            </p>
            <div style={{ animationDelay: '400ms' }} className={`mt-12 flex flex-col items-center justify-center gap-4 sm:flex-row ${isMounted ? 'animate-fadeInUp' : 'opacity-0'}`}>
              <div className="relative group rounded-full">
                <GlowingEffect
                  spread={40}
                  glow={true}
                  disabled={false}
                  proximity={64}
                  inactiveZone={0.01}
                  borderWidth={2}
                />
                <a href="#" className="relative flex w-full items-center justify-center rounded-full bg-white px-8 py-4 text-base font-bold text-black shadow-2xl transition hover:scale-105 hover:bg-white/90 sm:w-auto">
                  Get Started Free
                </a>
              </div>
              <a href="#" className="flex w-full items-center justify-center gap-2 rounded-full border border-white/20 bg-white/5 px-8 py-4 text-base font-bold text-white backdrop-blur-xl transition hover:border-white/40 hover:bg-white/10 sm:w-auto">
                How it Works
              </a>
            </div>
          </div>
        </div>

        {/* ================== PARTNERS ================== */}

        {/* ================== FOREGROUND ================== */}

        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-0 h-[50vh]">
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 flex h-full items-end gap-px px-[2px]">
            {pillars.map((h, i) => (
              <div
                key={i}
                className="flex-1 bg-black transition-height duration-1000 ease-in-out"
                style={{
                  height: isMounted ? `${h}%` : '0%',
                  transitionDelay: `${Math.abs(i - Math.floor(pillars.length / 2)) * 60}ms`
                }}
              />
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
