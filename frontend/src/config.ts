const env = import.meta.env;
export const config = {
  keycloakUrl: env.VITE_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: env.VITE_KEYCLOAK_REALM ?? "taskapp",
  clientId: env.VITE_KEYCLOAK_CLIENT_ID ?? "task-frontend",
  taskApi: env.VITE_TASK_API_URL ?? "http://localhost:8001",
  replicaApi: env.VITE_REPLICA_API_URL ?? "http://localhost:8002",
};
