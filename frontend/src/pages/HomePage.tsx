import { Link } from 'react-router-dom';
import { useProfiles } from '@/hooks/useProfiles';
import { Col, Row, Container } from 'react-bootstrap';
import { FaServer, FaDatabase, FaNetworkWired, FaCogs, FaArrowRight, FaExclamationTriangle } from 'react-icons/fa';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const features = [
  {
    title: 'Compute',
    description: 'Monitor EC2 instances, Lambda functions, ECS clusters, and EKS resources across your AWS accounts.',
    icon: FaServer,
    iconClass: 'compute',
    link: '/dashboard?view=compute',
    linkText: 'View Compute',
  },
  {
    title: 'Storage',
    description: 'Track S3 buckets, RDS databases, DynamoDB tables, and EBS volumes in one place.',
    icon: FaDatabase,
    iconClass: 'storage',
    link: '/dashboard?view=storage',
    linkText: 'View Storage',
  },
  {
    title: 'Networking',
    description: 'Visualize VPCs, subnets, security groups, and network configurations.',
    icon: FaNetworkWired,
    iconClass: 'network',
    link: '/dashboard?view=network',
    linkText: 'View Network',
  },
  {
    title: 'Services',
    description: 'Manage ALBs, CloudWatch metrics, IAM resources, and other AWS services.',
    icon: FaCogs,
    iconClass: 'services',
    link: '/dashboard?view=services',
    linkText: 'View Services',
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
          <div className="alert-modern alert-warning" style={{ maxWidth: '500px' }}>
            <FaExclamationTriangle size={20} />
            <div>
              <strong>No AWS Profile Configured</strong>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem' }}>
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
          <h2 style={{ fontWeight: 700, marginBottom: '1.5rem', color: 'var(--cs-gray-800)' }}>
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
