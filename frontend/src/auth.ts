import Keycloak from "keycloak-js";
import { config } from "./config";

export const keycloak = new Keycloak({
  url: config.keycloakUrl,
  realm: config.realm,
  clientId: config.clientId,
});

let initPromise: Promise<boolean> | null = null;

/** Redirects to Keycloak if unauthenticated (Authorization Code + PKCE). Safe under StrictMode. */
export function initAuth(): Promise<boolean> {
  if (!initPromise) {
    initPromise = keycloak
      .init({ onLoad: "login-required", pkceMethod: "S256", checkLoginIframe: false })
      .then((ok) => {
        // refresh the token before it expires
        setInterval(() => {
          keycloak.updateToken(60).catch(() => keycloak.login());
        }, 15_000);
        return ok;
      });
  }
  return initPromise;
}

export async function freshToken(): Promise<string> {
  try {
    await keycloak.updateToken(10);
  } catch {
    await keycloak.login();
  }
  return keycloak.token as string;
}

export const username = () =>
  (keycloak.tokenParsed?.preferred_username as string | undefined) ?? "user";

export const logout = () => keycloak.logout({ redirectUri: window.location.origin });
