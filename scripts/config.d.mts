import type { ClientConfiguration } from "@cv/api-client/configuration";
export const root: string;
export const python: string;
export function projection(
  component: string,
  configFile: string | undefined,
  profile: string | undefined,
): ClientConfiguration;
export function environment(component: string): ClientConfiguration;
