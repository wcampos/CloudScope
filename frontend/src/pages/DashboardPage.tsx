import { useSearchParams } from "react-router-dom";
import { useResources, useRefreshResources } from "@/hooks/useResources";
import ViewFilter, { type ViewType } from "@/components/dashboard/ViewFilter";
import ResourceTable from "@/components/dashboard/ResourceTable";
import RefreshButton from "@/components/dashboard/RefreshButton";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useNotification } from "@/context/NotificationContext";
import { Container } from "react-bootstrap";
import { useEffect, useMemo } from "react";
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
} from "react-icons/fa";
import type { ResourcesResponse } from "@/types/resource";

interface StatCardProps {
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  label: string;
  value: number;
}

function StatCard({ icon: Icon, iconBg, iconColor, label, value }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: iconBg, color: iconColor }}>
        <Icon />
      </div>
      <div className="stat-info">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

function countResources(resources: ResourcesResponse | undefined, categories: string[]): number {
  if (!resources) return 0;
  return Object.entries(resources).reduce((total, [name, items]) => {
    if (categories.some((c) => name.toLowerCase().includes(c))) {
      return total + (Array.isArray(items) ? items.length : 0);
    }
    return total;
  }, 0);
}

export default function DashboardPage() {
  const [searchParams] = useSearchParams();
  const view = (searchParams.get("view") as ViewType) || "all";
  const { data: resources, isLoading, isFetching, isError, error } = useResources();
  const refresh = useRefreshResources();
  const { notify } = useNotification();

  useEffect(() => {
    if (isError && error) {
      notify(String(error), "error");
    }
  }, [isError, error, notify]);

  const handleRefresh = () => {
    refresh.mutate(undefined, {
      onSuccess: () => notify("Resources refreshed", "success"),
      onError: (err) => notify(String(err), "error"),
    });
  };

  const stats = useMemo(
    () => ({
      compute: countResources(resources, ["ec2", "lambda", "ecs", "eks"]),
      data: countResources(resources, ["rds", "dynamodb", "documentdb"]),
      cache: countResources(resources, ["elasticache"]),
      storage: countResources(resources, ["s3"]),
      network: countResources(resources, [
        "vpc",
        "subnet",
        "security_group",
        "route_table",
        "internet_gateway",
        "nat_gateway",
      ]),
      messaging: countResources(resources, ["sqs", "sns"]),
      cdn: countResources(resources, ["cloudfront"]),
      api: countResources(resources, ["api gateway"]),
      services: countResources(resources, ["load balancer", "target group"]),
    }),
    [resources]
  );

  return (
    <Container className="py-4">
      {/* Page Header */}
      <div className="page-header">
        <h2>AWS Resources</h2>
        <div className="header-actions">
          <RefreshButton onClick={handleRefresh} isLoading={isFetching} />
        </div>
      </div>

      {/* Stats Grid */}
      {!isLoading && resources && (
        <div className="stats-grid">
          <StatCard
            icon={FaServer}
            iconBg="linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)"
            iconColor="#d97706"
            label="Compute"
            value={stats.compute}
          />
          <StatCard
            icon={FaDatabase}
            iconBg="linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)"
            iconColor="#2563eb"
            label="Data"
            value={stats.data}
          />
          <StatCard
            icon={FaMemory}
            iconBg="linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%)"
            iconColor="#b45309"
            label="Cache"
            value={stats.cache}
          />
          <StatCard
            icon={FaArchive}
            iconBg="linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)"
            iconColor="#1d4ed8"
            label="Storage"
            value={stats.storage}
          />
          <StatCard
            icon={FaNetworkWired}
            iconBg="linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)"
            iconColor="#059669"
            label="Network"
            value={stats.network}
          />
          <StatCard
            icon={FaEnvelope}
            iconBg="linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%)"
            iconColor="#0d9488"
            label="Messaging"
            value={stats.messaging}
          />
          <StatCard
            icon={FaGlobe}
            iconBg="linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)"
            iconColor="#ea580c"
            label="CDN"
            value={stats.cdn}
          />
          <StatCard
            icon={FaPlug}
            iconBg="linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)"
            iconColor="#4f46e5"
            label="API / Serverless"
            value={stats.api}
          />
          <StatCard
            icon={FaCogs}
            iconBg="linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%)"
            iconColor="#7c3aed"
            label="Services"
            value={stats.services}
          />
        </div>
      )}

      {/* View Filter */}
      <div style={{ marginBottom: "1.5rem" }}>
        <ViewFilter />
      </div>

      {/* Content */}
      {isLoading && <LoadingSpinner message="Loading resources..." />}
      {!isLoading && <ResourceTable resources={resources} view={view} />}
    </Container>
  );
}
