import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import App from './App';
import './styles/global.scss';
import './App.scss';

const root = ReactDOM.createRoot(document.getElementById('root')!);
const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!clerkPublishableKey) {
  root.render(
    <React.StrictMode>
      <main className="configuration-error">
        <h1>Authentication is not configured</h1>
        <p>
          Add VITE_CLERK_PUBLISHABLE_KEY to the frontend environment and restart
          the Vite development server.
        </p>
      </main>
    </React.StrictMode>,
  );
} else {
  root.render(
    <React.StrictMode>
      <ClerkProvider publishableKey={clerkPublishableKey}>
        <App />
      </ClerkProvider>
    </React.StrictMode>,
  );
}
