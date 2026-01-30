export type ResourceRow = Record<string, string | number | boolean | null>;

export interface ResourcesResponse {
  [serviceName: string]: ResourceRow[] | undefined;
}
