import apiClient from './client';

export interface HealthResponse {
  status: string;
  timestamp?: string;
  services?: {
    database?: {
      status: string;
      message?: string;
    };
    profiles?: {
      status: string;
      count?: number;
      message?: string;
    };
    active_profile?: {
      status: string;
      name?: string | null;
      message?: string;
    };
  };
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown' | 'checking';
  responseTime?: number;
  message?: string;
  timestamp?: string;
}

export async function healthCheck(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
}

export async function checkApiHealth(): Promise<ServiceHealth> {
  const start = performance.now();
  try {
    const response = await apiClient.get<HealthResponse>('/health', { timeout: 5000 });
    const responseTime = Math.round(performance.now() - start);
    return {
      name: 'API Service',
      status: response.data.status === 'healthy' || response.data.status === 'degraded' ? 'healthy' : 'unhealthy',
      responseTime,
      timestamp: response.data.timestamp,
      message: 'Flask API responding normally',
    };
  } catch (error) {
    const responseTime = Math.round(performance.now() - start);
    return {
      name: 'API Service',
      status: 'unhealthy',
      responseTime,
      message: error instanceof Error ? error.message : 'Failed to connect to API',
    };
  }
}

export async function checkDatabaseHealth(): Promise<ServiceHealth> {
  const start = performance.now();
  try {
    const response = await apiClient.get<HealthResponse>('/health', { timeout: 5000 });
    const responseTime = Math.round(performance.now() - start);
    const dbStatus = response.data.services?.database;
    const profilesStatus = response.data.services?.profiles;

    if (dbStatus?.status === 'healthy') {
      const profileCount = profilesStatus?.count ?? 0;
      return {
        name: 'Database (PostgreSQL)',
        status: 'healthy',
        responseTime,
        message: `Connected - ${profileCount} profile${profileCount !== 1 ? 's' : ''} stored`,
      };
    } else {
      return {
        name: 'Database (PostgreSQL)',
        status: 'unhealthy',
        responseTime,
        message: dbStatus?.message || 'Database connection failed',
      };
    }
  } catch (error) {
    const responseTime = Math.round(performance.now() - start);
    return {
      name: 'Database (PostgreSQL)',
      status: 'unhealthy',
      responseTime,
      message: error instanceof Error ? error.message : 'Cannot check database status',
    };
  }
}

export async function checkAwsConnection(): Promise<ServiceHealth> {
  const start = performance.now();
  try {
    // First check if there's an active profile
    const healthResponse = await apiClient.get<HealthResponse>('/health', { timeout: 5000 });
    const activeProfile = healthResponse.data.services?.active_profile;

    if (!activeProfile || activeProfile.status === 'none' || !activeProfile.name) {
      const responseTime = Math.round(performance.now() - start);
      return {
        name: 'AWS Connection',
        status: 'unknown',
        responseTime,
        message: 'No active AWS profile configured',
      };
    }

    // Try to fetch resources to verify AWS connection
    const response = await apiClient.get('/api/resources', { timeout: 15000 });
    const responseTime = Math.round(performance.now() - start);
    const resourceCount = response.data
      ? Object.values(response.data).reduce((sum: number, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0)
      : 0;
    return {
      name: 'AWS Connection',
      status: 'healthy',
      responseTime,
      message: `Connected via "${activeProfile.name}" - ${resourceCount} resources`,
    };
  } catch (error) {
    const responseTime = Math.round(performance.now() - start);
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';

    // Check for specific error types
    if (errorMsg.includes('No active profile') || errorMsg.includes('400')) {
      return {
        name: 'AWS Connection',
        status: 'unknown',
        responseTime,
        message: 'No active AWS profile configured',
      };
    }

    return {
      name: 'AWS Connection',
      status: 'unhealthy',
      responseTime,
      message: `AWS error: ${errorMsg}`,
    };
  }
}

export async function checkFrontendHealth(): Promise<ServiceHealth> {
  return {
    name: 'Frontend (React)',
    status: 'healthy',
    responseTime: 0,
    message: 'Application loaded successfully',
    timestamp: new Date().toISOString(),
  };
}

export async function getAllHealthChecks(): Promise<ServiceHealth[]> {
  const checks = await Promise.all([
    checkFrontendHealth(),
    checkApiHealth(),
    checkDatabaseHealth(),
    checkAwsConnection(),
  ]);
  return checks;
}
