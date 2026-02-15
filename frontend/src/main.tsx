import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./app/App";
import "./styles/index.css";
import "./app/i18n";
import CognitoProvider from "./components/CognitoProvider";
import { assertConfig } from "./lib/config";

let configError: string | null = null;
try {
  assertConfig();
} catch (err: unknown) {
  configError = err instanceof Error ? err.message : "Missing required configuration.";
}

const root = ReactDOM.createRoot(document.getElementById("root")!);

if (configError) {
  root.render(
    <React.StrictMode>
      <div className="min-h-screen bg-slate-50 px-4 py-10">
        <div className="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="text-lg font-semibold text-slate-900">Configuration error</div>
          <div className="mt-2 text-sm text-slate-700">{configError}</div>
          <div className="mt-4 text-xs text-slate-500">
            Missing `VITE_*` environment variables. For local development, check `frontend/.env.example`.
          </div>
        </div>
      </div>
    </React.StrictMode>
  );
} else {
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <CognitoProvider>
          <App />
        </CognitoProvider>
      </BrowserRouter>
    </React.StrictMode>
  );
}
