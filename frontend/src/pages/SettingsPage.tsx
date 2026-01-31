import { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import {
  FaCog,
  FaInfoCircle,
  FaServer,
  FaDatabase,
  FaCode,
  FaHeartbeat,
  FaSyncAlt,
  FaCheckCircle,
  FaTimesCircle,
  FaQuestionCircle,
  FaSpinner,
  FaAws,
  FaReact,
  FaMemory,
} from 'react-icons/fa';
import { getAllHealthChecks, type ServiceHealth } from '@/api/health';

const version = import.meta.env.VITE_APP_VERSION ?? '1.0.0';

/** Health check auto-refresh interval in minutes (configurable via VITE_HEALTH_CHECK_INTERVAL_MINUTES). */
const HEALTH_CHECK_INTERVAL_MINUTES = (() => {
  const v = import.meta.env.VITE_HEALTH_CHECK_INTERVAL_MINUTES;
  if (v === undefined || v === '') return 2;
  const n = Number(v);
  return Number.isFinite(n) && n >= 1 ? Math.min(n, 60) : 2;
})();
const HEALTH_CHECK_INTERVAL_MS = HEALTH_CHECK_INTERVAL_MINUTES * 60 * 1000;

function getStatusIcon(status: ServiceHealth['status']) {
  switch (status) {
    case 'healthy':
      return <FaCheckCircle style={{ color: 'var(--cs-success)' }} />;
    case 'unhealthy':
      return <FaTimesCircle style={{ color: 'var(--cs-danger)' }} />;
    case 'not_configured':
      return <FaQuestionCircle style={{ color: 'var(--cs-gray-500)' }} />;
    case 'unknown':
      return <FaQuestionCircle style={{ color: 'var(--cs-warning)' }} />;
    case 'checking':
      return <FaSpinner className="fa-spin" style={{ color: 'var(--cs-primary)' }} />;
    default:
      return <FaQuestionCircle style={{ color: 'var(--cs-gray-400)' }} />;
  }
}

function getStatusBg(status: ServiceHealth['status']) {
  switch (status) {
    case 'healthy':
      return 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)';
    case 'unhealthy':
      return 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)';
    case 'not_configured':
      return 'linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)';
    case 'unknown':
      return 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)';
    case 'checking':
      return 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)';
    default:
      return 'var(--cs-gray-100)';
  }
}

function getServiceIcon(name: string) {
  if (name.includes('Frontend')) return <FaReact />;
  if (name.includes('API')) return <FaServer />;
  if (name.includes('Database')) return <FaDatabase />;
  if (name.includes('Cache')) return <FaMemory />;
  if (name.includes('AWS')) return <FaAws />;
  return <FaServer />;
}

interface HealthCardProps {
  health: ServiceHealth;
}

function HealthCard({ health }: HealthCardProps) {
  return (
    <div
      style={{
        background: 'white',
        border: '1px solid var(--cs-gray-200)',
        borderRadius: 'var(--cs-radius-lg)',
        padding: '1.25rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '1rem',
        transition: 'var(--cs-transition)',
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: 'var(--cs-radius)',
          background: getStatusBg(health.status),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.25rem',
          flexShrink: 0,
        }}
      >
        {getServiceIcon(health.name)}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <span style={{ fontWeight: 600, color: 'var(--cs-gray-800)' }}>{health.name}</span>
          {getStatusIcon(health.status)}
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--cs-gray-500)', marginBottom: '0.5rem' }}>
          {health.message || 'Checking...'}
        </div>
        {health.responseTime !== undefined && health.responseTime > 0 && (
          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--cs-gray-400)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              background: 'var(--cs-gray-100)',
              padding: '0.25rem 0.5rem',
              borderRadius: 'var(--cs-radius-sm)',
            }}
          >
            Response: {health.responseTime}ms
          </div>
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [healthChecks, setHealthChecks] = useState<ServiceHealth[]>([
    { name: 'Frontend (React)', status: 'checking', message: 'Checking...' },
    { name: 'API Service', status: 'checking', message: 'Checking...' },
    { name: 'Database (PostgreSQL)', status: 'checking', message: 'Checking...' },
    { name: 'AWS Connection', status: 'checking', message: 'Checking...' },
  ]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const runHealthChecks = useCallback(async () => {
    setIsRefreshing(true);
    setHealthChecks((prev) =>
      prev.map((h) => ({ ...h, status: 'checking' as const, message: 'Checking...' }))
    );

    try {
      const results = await getAllHealthChecks();
      setHealthChecks(results);
      setLastChecked(new Date());
    } catch (error) {
      console.error('Health check failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    runHealthChecks();
    const interval = setInterval(runHealthChecks, HEALTH_CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [runHealthChecks]);

  const healthyCount = healthChecks.filter((h) => h.status === 'healthy').length;
  const notConfiguredCount = healthChecks.filter((h) => h.status === 'not_configured').length;
  const unhealthyCount = healthChecks.filter((h) => h.status === 'unhealthy').length;
  const totalCount = healthChecks.length;
  const okCount = healthyCount + notConfiguredCount;
  const overallStatus =
    unhealthyCount > 0 ? 'unhealthy' : okCount === totalCount ? 'healthy' : healthyCount > 0 ? 'partial' : 'unhealthy';

  return (
    <Container className="py-4">
      {/* Page Header */}
      <div className="page-header">
        <h2>
          <FaCog style={{ marginRight: '0.75rem', color: 'var(--cs-primary)' }} />
          Settings
        </h2>
      </div>

      {/* Health Check Dashboard */}
      <div className="card-modern mb-4">
        <div
          className="card-header"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FaHeartbeat style={{ color: 'var(--cs-danger)' }} />
            Service Health
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            {lastChecked && (
              <span style={{ fontSize: '0.75rem', color: 'var(--cs-gray-400)' }}>
                Last checked: {lastChecked.toLocaleTimeString()}
              </span>
            )}
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-gray-500)' }}>
              Auto-refresh every {HEALTH_CHECK_INTERVAL_MINUTES} {HEALTH_CHECK_INTERVAL_MINUTES === 1 ? 'minute' : 'minutes'}
            </span>
            {(() => {
              const cacheHealth = healthChecks.find((h) => h.name === 'Cache (Redis)');
              const cacheOk = cacheHealth?.status === 'healthy';
              return cacheHealth ? (
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: cacheOk ? 'var(--cs-success)' : 'var(--cs-gray-500)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                  }}
                  title={cacheHealth.message}
                >
                  Cache: {cacheOk ? '✓' : '—'} {cacheOk ? 'Redis' : cacheHealth.status === 'unhealthy' ? 'Unavailable' : ''}
                </span>
              ) : null;
            })()}
            <button
              className="btn-modern btn-modern-secondary"
              onClick={runHealthChecks}
              disabled={isRefreshing}
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
            >
              {isRefreshing ? (
                <>
                  <FaSpinner className="fa-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <FaSyncAlt />
                  Refresh
                </>
              )}
            </button>
          </div>
        </div>
        <div className="card-body">
          {/* Overall Status */}
          <div
            style={{
              background:
                overallStatus === 'healthy'
                  ? 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)'
                  : overallStatus === 'partial'
                  ? 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'
                  : 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
              borderRadius: 'var(--cs-radius-lg)',
              padding: '1.5rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div
                style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color:
                    overallStatus === 'healthy'
                      ? '#065f46'
                      : overallStatus === 'partial'
                      ? '#92400e'
                      : '#991b1b',
                  marginBottom: '0.25rem',
                }}
              >
                {overallStatus === 'healthy'
                  ? 'All Systems Operational'
                  : overallStatus === 'partial'
                  ? 'Partial Outage'
                  : 'System Issues Detected'}
              </div>
              <div
                style={{
                  fontSize: '0.9rem',
                  color:
                    overallStatus === 'healthy'
                      ? '#047857'
                      : overallStatus === 'partial'
                      ? '#b45309'
                      : '#b91c1c',
                }}
              >
                {healthyCount} of {totalCount} services healthy
                {notConfiguredCount > 0 && ` · ${notConfiguredCount} not configured`}
              </div>
            </div>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2rem',
              }}
            >
              {overallStatus === 'healthy' ? (
                <FaCheckCircle style={{ color: '#059669' }} />
              ) : overallStatus === 'partial' ? (
                <FaQuestionCircle style={{ color: '#d97706' }} />
              ) : (
                <FaTimesCircle style={{ color: '#dc2626' }} />
              )}
            </div>
          </div>

          {/* Individual Health Cards */}
          <Row className="g-3">
            {healthChecks.map((health) => (
              <Col key={health.name} md={6}>
                <HealthCard health={health} />
              </Col>
            ))}
          </Row>
        </div>
      </div>

      <Row className="g-4">
        {/* Version Info */}
        <Col lg={4}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaInfoCircle style={{ color: 'var(--cs-info)' }} />
              Version
            </div>
            <div className="card-body">
              <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                <div
                  style={{
                    fontSize: '2.5rem',
                    fontWeight: 700,
                    background: 'var(--cs-gradient-primary)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  v{version}
                </div>
                <div style={{ color: 'var(--cs-gray-500)', marginTop: '0.5rem' }}>CloudScope</div>
              </div>
            </div>
          </div>
        </Col>

        {/* Environment */}
        <Col lg={4}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaServer style={{ color: 'var(--cs-success)' }} />
              Environment
            </div>
            <div className="card-body">
              <div style={{ padding: '0.5rem 0' }}>
                <div className="profile-meta" style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--cs-gray-700)' }}>API Service</strong>
                  <div>Flask + Gunicorn</div>
                </div>
                <div className="profile-meta" style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--cs-gray-700)' }}>Frontend</strong>
                  <div>React SPA with Vite</div>
                </div>
                <div className="profile-meta">
                  <strong style={{ color: 'var(--cs-gray-700)' }}>Deployment</strong>
                  <div>Docker Compose</div>
                </div>
              </div>
            </div>
          </div>
        </Col>

        {/* Database */}
        <Col lg={4}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaDatabase style={{ color: 'var(--cs-warning)' }} />
              Storage
            </div>
            <div className="card-body">
              <div style={{ padding: '0.5rem 0' }}>
                <div className="profile-meta" style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--cs-gray-700)' }}>Database</strong>
                  <div>PostgreSQL 16</div>
                </div>
                <div className="profile-meta" style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ color: 'var(--cs-gray-700)' }}>Cache</strong>
                  <div>Redis 7</div>
                </div>
                <div className="profile-meta">
                  <strong style={{ color: 'var(--cs-gray-700)' }}>Profiles</strong>
                  <div>Encrypted credentials</div>
                </div>
              </div>
            </div>
          </div>
        </Col>
      </Row>

      {/* Tech Stack */}
      <div className="card-modern mt-4">
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FaCode style={{ color: 'var(--cs-primary)' }} />
          Technology Stack
        </div>
        <div className="card-body">
          <Row className="g-3">
            {[
              { name: 'React', version: '18.2', color: '#61dafb' },
              { name: 'TypeScript', version: '5.3', color: '#3178c6' },
              { name: 'Vite', version: '5.1', color: '#646cff' },
              { name: 'React Router', version: '6.x', color: '#ca4245' },
              { name: 'TanStack Query', version: '5.x', color: '#ff4154' },
              { name: 'Bootstrap', version: '5.3', color: '#7952b3' },
              { name: 'Axios', version: '1.6', color: '#5a29e4' },
              { name: 'React Icons', version: '5.x', color: '#e91e63' },
            ].map((tech) => (
              <Col key={tech.name} xs={6} sm={4} md={3}>
                <div
                  style={{
                    background: 'var(--cs-gray-50)',
                    borderRadius: 'var(--cs-radius)',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: tech.color,
                    }}
                  />
                  <span style={{ fontWeight: 500, color: 'var(--cs-gray-700)' }}>{tech.name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--cs-gray-400)', marginLeft: 'auto' }}>
                    {tech.version}
                  </span>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      </div>
    </Container>
  );
}
