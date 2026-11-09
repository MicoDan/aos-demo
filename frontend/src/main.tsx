import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { initAuth } from "./auth";
import { Brand } from "./components/Brand";
import "./styles.css";

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(<div className="boot"><Brand size={72} /><p>Redirecting to sign-in…</p></div>);

initAuth()
  .then(() =>
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    ),
  )
  .catch((e) => root.render(<div className="boot"><Brand size={72} /><p className="error">Could not reach the login server: {String(e)}</p></div>));
