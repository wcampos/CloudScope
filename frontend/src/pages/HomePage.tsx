import { Link } from "react-router-dom";
import { useProfiles } from "@/hooks/useProfiles";
import { Col, Row, Container } from "react-bootstrap";
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
  FaArrowRight,
  FaExclamationTriangle,
} from "react-icons/fa";
import LoadingSpinner from "@/components/common/LoadingSpinner";

const features = [
  {
    title: "Compute",
    description: "Monitor EC2 instances, Lambda functions, ECS clusters, and EKS clusters.",
    icon: FaServer,
    iconClass: "compute",
    link: "/dashboard?view=compute",
    linkText: "View Compute",
  },
  {
    title: "Data",
    description: "RDS instances, Aurora clusters, DynamoDB tables, and DocumentDB clusters.",
    icon: FaDatabase,
    iconClass: "data",
    link: "/dashboard?view=data",
    linkText: "View Data",
  },
  {
    title: "Cache",
    description: "ElastiCache clusters and in-memory cache systems.",
    icon: FaMemory,
    iconClass: "cache",
    link: "/dashboard?view=cache",
    linkText: "View Cache",
  },
  {
    title: "Storage",
    description: "S3 buckets and object storage.",
    icon: FaArchive,
    iconClass: "storage",
    link: "/dashboard?view=storage",
    linkText: "View Storage",
  },
  {
    title: "Networking",
    description: "VPCs, subnets, security groups, and network configurations.",
    icon: FaNetworkWired,
    iconClass: "network",
    link: "/dashboard?view=network",
    linkText: "View Network",
  },
  {
    title: "Messaging",
    description: "SQS queues and SNS topics.",
    icon: FaEnvelope,
    iconClass: "messaging",
    link: "/dashboard?view=messaging",
    linkText: "View Messaging",
  },
  {
    title: "CDN",
    description: "CloudFront distributions and edge caching.",
    icon: FaGlobe,
    iconClass: "cdn",
    link: "/dashboard?view=cdn",
    linkText: "View CDN",
  },
  {
    title: "API / Serverless",
    description: "API Gateway REST and HTTP APIs.",
    icon: FaPlug,
    iconClass: "api",
    link: "/dashboard?view=api",
    linkText: "View API",
  },
  {
    title: "Services",
    description: "Load balancers, target groups, and other AWS services.",
    icon: FaCogs,
    iconClass: "services",
    link: "/dashboard?view=services",
    linkText: "View Services",
  },
];

export default function HomePage() {
  const { data: profiles, isLoading } = useProfiles();
  const activeProfile = profiles?.find((p) => p.is_active);

  if (isLoading) {
    return <LoadingSpinner message="Loading profiles..." />;
  }

  return (
    <Container className="py-4">
      {/* Hero Section */}
      <div className="hero-section mb-5">
        <h1>Welcome to CloudScope</h1>
        <p className="lead">
          Your unified dashboard for monitoring and managing AWS resources across multiple accounts.
        </p>
        {activeProfile ? (
          <div className="profile-badge">
            <span className="badge-dot" />
            <span>
              Connected to <strong>{activeProfile.custom_name || activeProfile.name}</strong>
              <span style={{ opacity: 0.7 }}> ({activeProfile.aws_region})</span>
            </span>
          </div>
        ) : (
          <div className="alert-modern alert-warning" style={{ maxWidth: "500px" }}>
            <FaExclamationTriangle size={20} />
            <div>
              <strong>No AWS Profile Configured</strong>
              <p style={{ margin: "0.5rem 0 0", fontSize: "0.9rem" }}>
                Set up an AWS profile to start viewing your resources.
              </p>
              <Link to="/profiles" className="btn-modern btn-modern-primary mt-3">
                Configure Profile
                <FaArrowRight />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Feature Cards */}
      {activeProfile && (
        <>
          <h2 style={{ fontWeight: 700, marginBottom: "1.5rem", color: "var(--cs-gray-800)" }}>
            Explore Resources
          </h2>
          <Row className="g-4">
            {features.map((feature) => (
              <Col key={feature.title} md={6} lg={3}>
                <div className="feature-card">
                  <div className={`feature-icon ${feature.iconClass}`}>
                    <feature.icon />
                  </div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                  <div className="card-actions">
                    <Link to={feature.link} className="btn-modern btn-modern-primary">
                      {feature.linkText}
                      <FaArrowRight size={12} />
                    </Link>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </>
      )}
    </Container>
  );
}
