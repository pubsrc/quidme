import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./app/App";
import "./styles/index.css";
import "./app/i18n";
import CognitoProvider from "./components/CognitoProvider";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <CognitoProvider>
        <App />
      </CognitoProvider>
    </BrowserRouter>
  </React.StrictMode>
);
