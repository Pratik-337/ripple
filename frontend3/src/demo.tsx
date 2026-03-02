import React from "react";
import { Web3HeroAnimated } from "@/src/components/ui/animated-web3-landing-page";
import { ContainerScroll } from "@/src/components/ui/container-scroll-animation";
import { Box, Lock, Search, Settings, Sparkles, Zap, Shield, Users, MessageSquare, Waves } from "lucide-react";
import { GlowingEffect } from "@/src/components/ui/glowing-effect";
import { cn } from "@/src/lib/utils";

export default function DemoOne({ onSignIn }: { onSignIn?: () => void }) {
  return <Web3HeroAnimated onSignIn={onSignIn} />;
}

export function HeroScrollDemo() {
  return (
    <div className="flex flex-col overflow-hidden pt-20 md:pt-32">
      <ContainerScroll
        titleComponent={
          <>
            <h1 className="text-4xl font-semibold text-white">
              Visualize the impact of <br />
              <span className="text-4xl md:text-[5rem] font-bold mt-1 leading-none bg-gradient-to-r from-white to-white/40 bg-clip-text text-transparent">
                Every Change
              </span>
            </h1>
          </>
        }
      >
        <img
          src="https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=2070&auto=format&fit=crop"
          alt="Codebase visualization"
          className="mx-auto rounded-2xl object-cover h-full w-full object-center"
          draggable={false}
          referrerPolicy="no-referrer"
        />
      </ContainerScroll>
    </div>
  );
}

export function GlowingEffectDemo() {
  return (
    <div className="bg-transparent py-32 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-light tracking-tight text-white md:text-5xl">
            Powerful features for <br />
            <span className="bg-gradient-to-r from-white to-white/40 bg-clip-text text-transparent">modern engineering teams</span>
          </h2>
        </div>
        <ul className="grid grid-cols-1 grid-rows-none gap-4 md:grid-cols-12 md:grid-rows-3 lg:gap-4 xl:max-h-[34rem] xl:grid-rows-2">
          <GridItem
            area="md:[grid-area:1/1/2/7] xl:[grid-area:1/1/2/5]"
            icon={<Zap className="h-4 w-4 text-rose-400" />}
            title="Real-time Impact Analysis"
            description="Instantly see which parts of your codebase are affected by a proposed change before you even open a PR."
          />
          <GridItem
            area="md:[grid-area:1/7/2/13] xl:[grid-area:2/1/3/5]"
            icon={<Shield className="h-4 w-4 text-emerald-400" />}
            title="Automated Review Routing"
            description="Ripple automatically identifies the right subject matter experts and routes reviews to the people who actually know the code."
          />
          <GridItem
            area="md:[grid-area:2/1/3/7] xl:[grid-area:1/5/3/8]"
            icon={<Users className="h-4 w-4 text-blue-400" />}
            title="Team Orchestration"
            description="Coordinate large-scale refactors across multiple teams with shared visibility and progress tracking."
          />
          <GridItem
            area="md:[grid-area:2/7/3/13] xl:[grid-area:1/8/2/13]"
            icon={<MessageSquare className="h-4 w-4 text-amber-400" />}
            title="Contextual Notifications"
            description="No more Slack noise. Get notified only when a change actually impacts your domain or dependencies."
          />
          <GridItem
            area="md:[grid-area:3/1/4/13] xl:[grid-area:2/8/3/13]"
            icon={<Search className="h-4 w-4 text-purple-400" />}
            title="Dependency Graphing"
            description="Explore your codebase's hidden connections with an interactive, living dependency map that updates with every commit."
          />
        </ul>
      </div>
    </div>
  );
}

export function AgentEraSection() {
  return (
    <section className="bg-transparent py-24 px-6 md:py-32 border-t border-white/5">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 md:items-end">
          <div>
            <h2 className="text-4xl font-light tracking-tight text-white md:text-5xl lg:text-6xl">
              Built for developers <br />
              <span className="bg-gradient-to-r from-white to-white/40 bg-clip-text text-transparent">for the agent-first era</span>
            </h2>
          </div>
          <div className="max-w-md md:ml-auto">
            <p className="text-lg leading-relaxed text-white/60">
              Ripple is built for user trust, whether you're a professional developer working in a large enterprise codebase, a hobbyist vibe-coding in their spare time, or anyone in between.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="bg-transparent border-t border-white/10 py-12 px-6">
      <div className="mx-auto max-w-7xl flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-white text-black">
            <Waves className="h-4 w-4" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">Ripple</span>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 text-sm font-medium text-white/50">
          {['About Ripple', 'Ripple Products', 'Privacy', 'Terms'].map((link) => (
            <a key={link} href="#" className="hover:text-white transition-colors">
              {link}
            </a>
          ))}
        </nav>
      </div>
    </footer>
  );
}

interface GridItemProps {
  area: string;
  icon: React.ReactNode;
  title: string;
  description: React.ReactNode;
}

const GridItem = ({ area, icon, title, description }: GridItemProps) => {
  return (
    <li className={cn("min-h-[14rem] list-none", area)}>
      <div className="relative h-full rounded-[1.25rem] border-[0.75px] border-white/10 p-2 md:rounded-[1.5rem] md:p-3">
        <GlowingEffect
          spread={40}
          glow={true}
          disabled={false}
          proximity={64}
          inactiveZone={0.01}
          borderWidth={3}
        />
        <div className="relative flex h-full flex-col justify-between gap-6 overflow-hidden rounded-xl border-[0.75px] border-white/10 bg-zinc-900/50 p-6 shadow-sm md:p-6">
          <div className="relative flex flex-1 flex-col justify-between gap-3">
            <div className="w-fit rounded-lg border-[0.75px] border-white/10 bg-white/5 p-2">
              {icon}
            </div>
            <div className="space-y-3">
              <h3 className="pt-0.5 text-xl leading-[1.375rem] font-semibold font-sans tracking-[-0.04em] md:text-2xl md:leading-[1.875rem] text-balance text-white">
                {title}
              </h3>
              <h2 className="font-sans text-sm leading-[1.125rem] md:text-base md:leading-[1.375rem] text-white/60">
                {description}
              </h2>
            </div>
          </div>
        </div>
      </div>
    </li>
  );
};
