import { Link, useSearchParams } from "react-router-dom";
import {
  FaLayerGroup,
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

const VIEWS = [
  { key: "all", label: "All Resources", icon: FaLayerGroup },
  { key: "compute", label: "Compute", icon: FaServer },
  { key: "data", label: "Data", icon: FaDatabase },
  { key: "cache", label: "Cache", icon: FaMemory },
  { key: "storage", label: "Storage", icon: FaArchive },
  { key: "network", label: "Network", icon: FaNetworkWired },
  { key: "messaging", label: "Messaging", icon: FaEnvelope },
  { key: "cdn", label: "CDN", icon: FaGlobe },
  { key: "api", label: "API / Serverless", icon: FaPlug },
  { key: "services", label: "Services", icon: FaCogs },
] as const;

export type ViewType = (typeof VIEWS)[number]["key"];

export default function ViewFilter() {
  const [searchParams] = useSearchParams();
  const current = (searchParams.get("view") as ViewType) || "all";

  return (
    <div className="view-filter">
      {VIEWS.map(({ key, label, icon: Icon }) => (
        <Link
          key={key}
          to={key === "all" ? "/dashboard" : `/dashboard?view=${key}`}
          className={`filter-pill ${current === key ? "active" : ""}`}
        >
          <Icon style={{ marginRight: "0.375rem" }} />
          {label}
        </Link>
      ))}
    </div>
  );
}
