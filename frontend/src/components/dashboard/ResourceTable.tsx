import { useState } from "react";
import DataTable from "@/components/common/DataTable";
import type { ResourcesResponse, ResourceRow } from "@/types/resource";
import type { ViewType } from "./ViewFilter";
import {
  FaServer,
  FaDatabase,
  FaMemory,
  FaArchive,
  FaNetworkWired,
  FaEnvelope,
  FaGlobe,
  FaPlug,
  FaCogs,
  FaFolder,
  FaChevronDown,
  FaChevronRight,
} from "react-icons/fa";

const SERVICE_CATEGORIES: Record<ViewType, string[]> = {
  all: [],
  compute: ["ec2", "lambda", "ecs", "eks"],
  data: ["rds", "dynamodb", "documentdb"],
  cache: ["elasticache"],
  storage: ["s3"],
  network: ["vpc", "subnet", "security_group", "route_table", "internet_gateway", "nat_gateway"],
  messaging: ["sqs", "sns"],
  cdn: ["cloudfront"],
  api: ["api gateway"],
  services: ["load balancer", "target group"],
};

function getServiceIcon(serviceName: string) {
  const name = serviceName.toLowerCase();
  if (["ec2", "lambda", "ecs", "eks"].some((s) => name.includes(s))) {
    return <FaServer style={{ color: "#d97706" }} />;
  }
  if (["rds", "dynamodb", "documentdb"].some((s) => name.includes(s))) {
    return <FaDatabase style={{ color: "#2563eb" }} />;
  }
  if (["elasticache"].some((s) => name.includes(s))) {
    return <FaMemory style={{ color: "#b45309" }} />;
  }
  if (["s3"].some((s) => name.includes(s))) {
    return <FaArchive style={{ color: "#1d4ed8" }} />;
  }
  if (
    ["vpc", "subnet", "security_group", "route_table", "internet_gateway", "nat_gateway"].some(
      (s) => name.includes(s)
    )
  ) {
    return <FaNetworkWired style={{ color: "#059669" }} />;
  }
  if (["sqs", "sns"].some((s) => name.includes(s))) {
    return <FaEnvelope style={{ color: "#0d9488" }} />;
  }
  if (["cloudfront"].some((s) => name.includes(s))) {
    return <FaGlobe style={{ color: "#ea580c" }} />;
  }
  if (["api gateway"].some((s) => name.includes(s))) {
    return <FaPlug style={{ color: "#4f46e5" }} />;
  }
  if (["load balancer", "target group", "alb", "cloudwatch", "iam"].some((s) => name.includes(s))) {
    return <FaCogs style={{ color: "#7c3aed" }} />;
  }
  return <FaFolder style={{ color: "#64748b" }} />;
}

function filterResources(resources: ResourcesResponse, view: ViewType): ResourcesResponse {
  if (!resources || view === "all") return resources ?? {};
  const categories = SERVICE_CATEGORIES[view];
  const filtered: ResourcesResponse = {};
  for (const [name, items] of Object.entries(resources)) {
    if (categories.some((c) => name.toLowerCase().includes(c))) {
      filtered[name] = items;
    }
  }
  return filtered;
}

interface ResourceTableProps {
  resources: ResourcesResponse | undefined;
  view: ViewType;
}

export default function ResourceTable({ resources, view }: ResourceTableProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const filtered = resources ? filterResources(resources, view) : {};
  const entries = Object.entries(filtered).filter(
    ([_, items]) => Array.isArray(items) && items.length > 0
  ) as [string, ResourceRow[]][];

  const toggle = (serviceName: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(serviceName)) next.delete(serviceName);
      else next.add(serviceName);
      return next;
    });
  };

  if (entries.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <FaFolder />
        </div>
        <h3>No Resources Found</h3>
        <p>
          No resources found for the selected view. Try selecting a different category or refresh
          your data.
        </p>
      </div>
    );
  }

  return (
    <>
      {entries.map(([serviceName, items]) => {
        const isExpanded = expanded.has(serviceName);
        return (
          <div key={serviceName} className="resource-card">
            <button
              type="button"
              className="resource-header"
              onClick={() => toggle(serviceName)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "0.5rem",
                padding: "0.75rem 1rem",
                border: "none",
                background: "var(--cs-gray-50)",
                cursor: "pointer",
                borderRadius: "var(--cs-radius)",
                textAlign: "left",
              }}
              aria-expanded={isExpanded}
            >
              <h3
                className="resource-title"
                style={{ margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}
              >
                {isExpanded ? (
                  <FaChevronDown style={{ fontSize: "0.75rem", color: "var(--cs-gray-500)" }} />
                ) : (
                  <FaChevronRight style={{ fontSize: "0.75rem", color: "var(--cs-gray-500)" }} />
                )}
                {getServiceIcon(serviceName)}
                {serviceName}
              </h3>
              <span className="resource-count">{items.length} items</span>
            </button>
            {isExpanded && (
              <div style={{ padding: "0" }}>
                <DataTable data={items} />
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}
