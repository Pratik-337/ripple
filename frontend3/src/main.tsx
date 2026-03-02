import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
//added 1 line
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import App from './App.tsx';
import { ErrorBoundary } from './components/ErrorBoundary.tsx';
import './index.css';

import { authStore } from './lib/authStore';

const root = document.getElementById('root')!;

//added 1 line
const queryClient = new QueryClient();

authStore.getState().refresh().catch(() => { }).finally(() => {
  createRoot(root).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary onGoHome={() => { window.location.reload(); }}>
          <App />
        </ErrorBoundary>
      </QueryClientProvider>
    </StrictMode>,
  );
});

