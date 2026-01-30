import DataTable from '@/components/common/DataTable';
import type { ResourcesResponse, ResourceRow } from '@/types/resource';
import type { ViewType } from './ViewFilter';
import { FaServer, FaDatabase, FaNetworkWired, FaCogs, FaFolder } from 'react-icons/fa';

const SERVICE_CATEGORIES: Record<ViewType, string[]> = {
  all: [],
  compute: ['ec2', 'lambda', 'ecs', 'eks'],
  storage: ['s3', 'ebs', 'efs', 'rds'],
  network: ['vpc', 'subnet', 'security_group', 'route_table', 'internet_gateway', 'nat_gateway'],
  services: ['alb', 'dynamodb', 'cloudwatch', 'iam'],
};

function getServiceIcon(serviceName: string) {
  const name = serviceName.toLowerCase();
  if (['ec2', 'lambda', 'ecs', 'eks'].some((s) => name.includes(s))) {
    return <FaServer style={{ color: '#d97706' }} />;
  }
  if (['s3', 'ebs', 'efs', 'rds', 'dynamodb'].some((s) => name.includes(s))) {
    return <FaDatabase style={{ color: '#2563eb' }} />;
  }
  if (['vpc', 'subnet', 'security_group', 'route_table', 'internet_gateway', 'nat_gateway'].some((s) => name.includes(s))) {
    return <FaNetworkWired style={{ color: '#059669' }} />;
  }
  if (['alb', 'cloudwatch', 'iam'].some((s) => name.includes(s))) {
    return <FaCogs style={{ color: '#7c3aed' }} />;
  }
  return <FaFolder style={{ color: '#64748b' }} />;
}

function filterResources(resources: ResourcesResponse, view: ViewType): ResourcesResponse {
  if (!resources || view === 'all') return resources ?? {};
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
  const filtered = resources ? filterResources(resources, view) : {};
  const entries = Object.entries(filtered).filter(
    ([_, items]) => Array.isArray(items) && items.length > 0
  ) as [string, ResourceRow[]][];

  if (entries.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">
          <FaFolder />
        </div>
        <h3>No Resources Found</h3>
        <p>No resources found for the selected view. Try selecting a different category or refresh your data.</p>
      </div>
    );
  }

  return (
    <>
      {entries.map(([serviceName, items]) => (
        <div key={serviceName} className="resource-card">
          <div className="resource-header">
            <h3 className="resource-title">
              {getServiceIcon(serviceName)}
              {serviceName}
            </h3>
            <span className="resource-count">{items.length} items</span>
          </div>
          <div style={{ padding: '0' }}>
            <DataTable data={items} />
          </div>
        </div>
      ))}
    </>
  );
}
