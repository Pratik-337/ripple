import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import { ErrorBoundary } from './components/ErrorBoundary.tsx';
import './index.css';

const root = document.getElementById('root')!;

createRoot(root).render(
  <StrictMode>
    <ErrorBoundary onGoHome={() => { window.location.reload(); }}>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);

