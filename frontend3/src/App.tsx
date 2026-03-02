import React, { useState, useEffect } from 'react';
import DemoOne, { HeroScrollDemo, GlowingEffectDemo, AgentEraSection, Footer } from './demo';
import { useRippleSocket } from './hooks/useRippleSocket';
import { authStore } from './lib/authStore';
import { AuthPage } from './components/AuthPage';
import { HomePage } from './components/HomePage';
import { ProjectOverviewPage } from './components/ProjectOverviewPage';
import { MonacoIDEPage } from './components/MonacoIDEPage';
import { ChangeReviewPage } from './components/ChangeReviewPage';
import { DependencyGraphPage } from './components/DependencyGraphPage';
import { VersionHistoryPage } from './components/VersionHistoryPage';
import { ProjectSettingsPage } from './components/ProjectSettingsPage';
import { NotFoundPage } from './components/NotFoundPage';
import { UserProfilePage } from './components/UserProfilePage';
import { GlobalNotificationsPage } from './components/GlobalNotificationsPage';
import { GlobalChangesPage } from './components/GlobalChangesPage';
import { GlobalTeamsPage } from './components/GlobalTeamsPage';
import { GlobalSettingsPage } from './components/GlobalSettingsPage';
import { SpotlightCursor } from './components/ui/spotlight-cursor';
import { Particles } from './components/ui/particles';

type ActiveView =
  | { type: 'landing' }
  | { type: 'auth' }
  | { type: 'auth-callback' }
  | { type: 'dashboard' }
  | { type: 'project'; projectId: string }
  | { type: 'ide'; projectId: string; componentId: string; componentName: string; readOnly: boolean }
  | { type: 'graph'; projectId: string }
  | { type: 'history'; projectId: string }
  | { type: 'change'; projectId: string; changeId: string }
  | { type: 'settings'; projectId: string }
  | { type: 'not-found' }
  | { type: 'profile' }
  | { type: 'global-notifications' }
  | { type: 'global-changes' }
  | { type: 'global-teams' }
  | { type: 'global-settings' };

export default function App() {
  const [view, setView] = useState<ActiveView>(() => {
    // Initial view resolution based on isAuthenticated and pathname
    const isCallback = window.location.pathname === '/auth/callback';
    if (isCallback) return { type: 'auth-callback' };

    // Fallback logic, but since main.tsx waits for refresh() we can check authStore
    const isAuth = authStore.getState().isInitialized && authStore.getState().accessToken;
    return isAuth ? { type: 'dashboard' } : { type: 'landing' };
  });

  useEffect(() => {
    // Automatically redirect to auth-callback if pathname matches, just in case
    if (window.location.pathname === '/auth/callback' && view.type !== 'auth-callback') {
      setView({ type: 'auth-callback' });
    }
  }, [view.type]);

  useEffect(() => {
    if (view.type === 'auth-callback') {
      authStore.getState().refresh()
        .then(() => {
          window.history.replaceState({}, document.title, "/");
          setView({ type: 'dashboard' });
        })
        .catch(() => {
          window.history.replaceState({}, document.title, "/");
          setView({ type: 'landing' });
        });
    }
  }, [view.type]);

  const isAuthedObj = authStore.getState().isInitialized && !!authStore.getState().accessToken;
  const shouldMountSocket = isAuthedObj && view.type !== 'auth' && view.type !== 'landing' && view.type !== 'auth-callback';

  const SocketProvider = ({ children }: { children: React.ReactNode }) => {
    useRippleSocket();
    return <>{children}</>;
  };

  if (view.type === 'auth-callback') {
    return (
      <div className="flex h-screen items-center justify-center bg-black text-white">
        Processing login...
      </div>
    );
  }

  // Landing page — no wrapper, keep original font scale
  if (view.type === 'landing') {
    return (
      <main className="bg-black relative min-h-screen">
        <div className="fixed inset-0 z-0 h-full w-full pointer-events-none">
          <Particles quantity={300} className="absolute inset-0 h-full w-full" color="#ffffff" />
        </div>
        <div className="relative z-10 hidden md:block">
          <SpotlightCursor />
        </div>
        <div className="relative z-10">
          <DemoOne onSignIn={() => setView({ type: 'auth' })} />
          <HeroScrollDemo />
          <GlowingEffectDemo />
          <AgentEraSection />
          <Footer />
        </div>
      </main>
    );
  }

  // Auth / sign-in — no wrapper, keep original font scale
  if (view.type === 'auth') {
    return (
      <AuthPage
        onBack={() => setView({ type: 'landing' })}
      />
    );
  }

  // ── All app-shell pages — wrapped with font scale bump ──────────────────

  const renderView = () => {
    if (view.type === 'settings') {
      return (
        <ProjectSettingsPage
          projectId={view.projectId}
          onBack={() => setView({ type: 'project', projectId: view.projectId })}
          onDeleted={() => setView({ type: 'dashboard' })}
          onArchived={() => setView({ type: 'dashboard' })}
        />
      );
    }

    if (view.type === 'history') {
      return (
        <VersionHistoryPage
          projectId={view.projectId}
          onBack={() => setView({ type: 'project', projectId: view.projectId })}
          onReviewChange={(pid, chid) => setView({ type: 'change', projectId: pid, changeId: chid })}
        />
      );
    }

    if (view.type === 'graph') {
      return (
        <DependencyGraphPage
          projectId={view.projectId}
          onBack={() => setView({ type: 'project', projectId: view.projectId })}
          onOpenIDE={(pid, cid, name, ro) => setView({ type: 'ide', projectId: pid, componentId: cid, componentName: name, readOnly: ro })}
        />
      );
    }

    if (view.type === 'change') {
      return (
        <ChangeReviewPage
          projectId={view.projectId}
          changeId={view.changeId}
          onBack={() => setView({ type: 'project', projectId: view.projectId })}
          onMerged={() => setView({ type: 'project', projectId: view.projectId })}
        />
      );
    }

    if (view.type === 'ide') {
      return (
        <MonacoIDEPage
          projectId={view.projectId}
          componentId={view.componentId}
          componentName={view.componentName}
          readOnly={view.readOnly}
          onBack={() => setView({ type: 'project', projectId: view.projectId })}
          onChangeSubmitted={(changeId) => setView({ type: 'project', projectId: view.projectId })}
        />
      );
    }

    if (view.type === 'project') {
      return (
        <ProjectOverviewPage
          projectId={view.projectId}
          onBack={() => setView({ type: 'dashboard' })}
          onOpenIDE={(pid, cid, name, ro) => setView({ type: 'ide', projectId: pid, componentId: cid, componentName: name, readOnly: ro })}
          onViewGraph={(pid) => setView({ type: 'graph', projectId: pid })}
          onViewHistory={(pid) => setView({ type: 'history', projectId: pid })}
          onReviewChange={(pid, chid) => setView({ type: 'change', projectId: pid, changeId: chid })}
          onOpenSettings={(pid) => setView({ type: 'settings', projectId: pid })}
        />
      );
    }

    if (view.type === 'profile') {
      return <UserProfilePage onBack={() => setView({ type: 'dashboard' })} />;
    }

    if (view.type === 'not-found') {
      return (
        <NotFoundPage
          onGoHome={() => setView({ type: 'landing' })}
          onGoToDashboard={() => setView({ type: 'dashboard' })}
        />
      );
    }

    if (view.type === 'global-notifications') {
      return <GlobalNotificationsPage onBack={() => setView({ type: 'dashboard' })} />;
    }

    if (view.type === 'global-changes') {
      return <GlobalChangesPage onBack={() => setView({ type: 'dashboard' })} />;
    }

    if (view.type === 'global-teams') {
      return <GlobalTeamsPage onBack={() => setView({ type: 'dashboard' })} />;
    }

    if (view.type === 'global-settings') {
      return <GlobalSettingsPage onBack={() => setView({ type: 'dashboard' })} />;
    }

    // dashboard (default app-shell view)
    return (
      <HomePage
        onLogout={() => setView({ type: 'landing' })}
        onProjectClick={(projectId) => setView({ type: 'project', projectId })}
        onOpenProfile={() => setView({ type: 'profile' })}
        onOpenView={(viewType) => setView({ type: viewType })}
      />
    );
  };

  const content = <div className="ripple-app">{renderView()}</div>;
  return shouldMountSocket ? <SocketProvider>{content}</SocketProvider> : content;
}
