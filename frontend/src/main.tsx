import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { initAuth } from "./auth";
import "./styles.css";

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(<p className="boot">Redirecting to sign-in…</p>);

initAuth()
  .then(() =>
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    ),
  )
  .catch((e) => root.render(<p className="boot error">Could not reach the login server: {String(e)}</p>));
