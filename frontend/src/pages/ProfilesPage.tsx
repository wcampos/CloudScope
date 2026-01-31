import { useState } from 'react';
import { Modal, Form, Container, Row, Col, Nav } from 'react-bootstrap';
import ProfileForm from '@/components/profiles/ProfileForm';
import ProfileCard from '@/components/profiles/ProfileCard';
import ConfigParser from '@/components/profiles/ConfigParser';
import CredentialParser from '@/components/profiles/CredentialParser';
import SetRoleForm from '@/components/profiles/SetRoleForm';
import {
  useProfiles,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
  useSetActiveProfile,
  useParseConfig,
  useParseCredentials,
  useCreateProfileFromRole,
} from '@/hooks/useProfiles';
import { useNotification } from '@/context/NotificationContext';
import type { Profile, ProfileFormData } from '@/types/profile';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { FaUserCog, FaCheckCircle, FaPlus, FaPaste, FaUserShield } from 'react-icons/fa';

export default function ProfilesPage() {
  const { data: profiles = [], isLoading, isError, error, refetch, isRefetching } = useProfiles();
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const deleteProfile = useDeleteProfile();
  const setActiveProfile = useSetActiveProfile();
  const parseConfig = useParseConfig();
  const parseCredentials = useParseCredentials();
  const createProfileFromRole = useCreateProfileFromRole();
  const { notify } = useNotification();
  const [pasteFormat, setPasteFormat] = useState<'config' | 'credentials'>('credentials');

  const [addTab, setAddTab] = useState<'profile' | 'role' | 'paste'>('profile');
  const [listTab, setListTab] = useState<'all' | 'active'>('all');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editModalShow, setEditModalShow] = useState(false);
  const [editProfile, setEditProfile] = useState<Profile | null>(null);
  const [editCustomName, setEditCustomName] = useState('');
  const [editRegion, setEditRegion] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const handleCreate = (data: ProfileFormData) => {
    createProfile.mutate(data, {
      onSuccess: () => notify('Profile added successfully', 'success'),
      onError: (err: { response?: { data?: { error?: string; detail?: string | string[] } }; message?: string }) => {
        const data = err.response?.data;
        const message =
          (data?.detail != null
            ? Array.isArray(data.detail)
              ? data.detail.join(', ')
              : String(data.detail)
            : data?.error) ?? (err as Error).message ?? 'Failed to add profile';
        notify(message, 'error');
      },
    });
  };

  const handleParseConfig = (configText: string) => {
    parseConfig.mutate(configText, {
      onSuccess: (created) => {
        if (created.length === 0) {
          notify(
            'No profiles created from config. Each section needs role_arn and source_profile; source_profile must already exist here (add it under "Add new profile" first).',
            'info'
          );
        } else if (created.length === 1) {
          notify(`Profile "${created[0].name}" imported`, 'success');
        } else {
          notify(`${created.length} profiles imported: ${created.map((p) => p.name).join(', ')}`, 'success');
        }
      },
      onError: (err: { response?: { data?: { error?: string; detail?: string | string[] } }; message?: string }) => {
        const data = err.response?.data;
        const message =
          data?.detail != null
            ? Array.isArray(data.detail)
              ? data.detail.join(', ')
              : String(data.detail)
            : (data as { error?: string })?.error ?? (err as Error).message ?? 'Failed to import config';
        notify(message, 'error');
      },
    });
  };

  const handleParseCredentials = (credentialsText: string) => {
    parseCredentials.mutate(credentialsText, {
      onSuccess: (profile) => notify(`Profile "${profile.name}" imported`, 'success'),
      onError: (err: { response?: { data?: { error?: string; detail?: string | string[] } }; message?: string }) => {
        const data = err.response?.data;
        const message =
          data?.detail != null
            ? Array.isArray(data.detail)
              ? data.detail.join(', ')
              : String(data.detail)
            : (data as { error?: string })?.error ?? (err as Error).message ?? 'Failed to import credentials';
        notify(message, 'error');
      },
    });
  };

  const handleCreateFromRole = (data: Parameters<typeof createProfileFromRole.mutate>[0]) => {
    createProfileFromRole.mutate(data, {
      onSuccess: (profile) => {
        notify(`Profile "${profile.name}" added (role)`, 'success');
      },
      onError: (err: { response?: { data?: { detail?: string | string[] } }; message?: string }) => {
        const data = err.response?.data;
        const message =
          data?.detail != null
            ? Array.isArray(data.detail)
              ? data.detail.join(', ')
              : String(data.detail)
            : (err as Error).message ?? 'Failed to add profile with role';
        notify(message, 'error');
      },
    });
  };

  const openEdit = (p: Profile) => {
    setEditProfile(p);
    setEditCustomName(p.custom_name ?? '');
    setEditRegion(p.aws_region);
    setEditModalShow(true);
  };

  const handleEditSave = () => {
    if (!editProfile) return;
    updateProfile.mutate(
      { id: editProfile.id, data: { custom_name: editCustomName, aws_region: editRegion } },
      {
        onSuccess: () => {
          notify('Profile updated', 'success');
          setEditModalShow(false);
          setEditProfile(null);
        },
        onError: (err) => notify(String(err), 'error'),
      }
    );
  };

  const handleDelete = (id: number) => {
    if (deleteConfirmId === id) {
      deleteProfile.mutate(id, {
        onSuccess: () => {
          notify('Profile deleted', 'success');
          setDeleteConfirmId(null);
        },
        onError: (err) => notify(String(err), 'error'),
      });
    } else {
      setDeleteConfirmId(id);
      setTimeout(() => setDeleteConfirmId(null), 3000);
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading profiles..." />;

  if (isError) {
    const isNetworkError =
      error instanceof Error &&
      (error.message === 'Network Error' || (error as { code?: string }).code === 'ERR_NETWORK');
    return (
      <Container className="py-4">
        <div className="page-header">
          <h2>
            <FaUserCog style={{ marginRight: '0.75rem', color: 'var(--cs-primary)' }} />
            AWS Profiles
          </h2>
        </div>
        <div className="card-modern" style={{ padding: '2rem', textAlign: 'center', maxWidth: '32rem', margin: '0 auto' }}>
          <p style={{ color: 'var(--cs-danger)', marginBottom: '0.5rem', fontWeight: 600 }}>
            Failed to load profiles
          </p>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-gray-600)', marginBottom: '1rem' }}>
            {error instanceof Error ? error.message : String(error)}
          </p>
          {isNetworkError && (
            <div
              style={{
                textAlign: 'left',
                fontSize: '0.8125rem',
                color: 'var(--cs-gray-600)',
                background: 'var(--cs-gray-50)',
                padding: '1rem',
                borderRadius: 'var(--cs-radius)',
                marginBottom: '1rem',
              }}
            >
              <strong style={{ color: 'var(--cs-gray-800)' }}>Make sure the API is running:</strong>
              <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.25rem' }}>
                <li><strong>Dev (npm run dev):</strong> Run API on port 5001: <code style={{ fontSize: '0.75rem' }}>cd api && uvicorn main:app --host 0.0.0.0 --port 5001</code>. DB: <code style={{ fontSize: '0.75rem' }}>docker compose up -d db</code> then set <code style={{ fontSize: '0.75rem' }}>DATABASE_URL=postgresql://cloudscope:cloudscope@localhost:5432/cloudscope</code> in <code style={{ fontSize: '0.75rem' }}>api/.env</code>.</li>
                <li><strong>Docker:</strong> Run <code style={{ fontSize: '0.75rem' }}>docker compose up -d</code>, open <strong>http://localhost:3000</strong> (not 5173). Check API: <a href="/health" target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem' }}>/health</a> or <a href="http://localhost:5001/health" target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem' }}>localhost:5001/health</a>.</li>
              </ul>
            </div>
          )}
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button type="button" className="btn-modern btn-modern-primary" onClick={() => refetch()}>
              Try again
            </button>
            <a
              href="/health"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-modern btn-modern-outline"
              style={{ padding: '0.5rem 0.75rem', fontSize: '0.875rem', textDecoration: 'none' }}
            >
              Open /health in new tab
            </a>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      {/* Page Header */}
      <div className="page-header">
        <h2>
          <FaUserCog style={{ marginRight: '0.75rem', color: 'var(--cs-primary)' }} />
          AWS Profiles
        </h2>
      </div>

      <Row className="g-4">
        {/* Left box: Add profile — subtabs Add new profile | Import by paste | Set role */}
        <Col lg={6}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaUserCog style={{ color: 'var(--cs-primary)' }} />
              Add AWS profile
            </div>
            <div className="card-body">
              {/* Subtab bar: Add new profile | Import by paste | Set role */}
              <div
                role="tablist"
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                  marginBottom: '1.25rem',
                  paddingBottom: '1rem',
                  borderBottom: '1px solid var(--cs-gray-200)',
                }}
              >
                <button
                  type="button"
                  role="tab"
                  aria-selected={addTab === 'profile'}
                  onClick={() => setAddTab('profile')}
                  style={{
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    borderRadius: 'var(--cs-radius)',
                    border: '1px solid ' + (addTab === 'profile' ? 'var(--cs-primary)' : 'var(--cs-gray-300)'),
                    color: addTab === 'profile' ? '#fff' : 'var(--cs-gray-700)',
                    background: addTab === 'profile' ? 'var(--cs-primary)' : 'var(--cs-gray-50)',
                    cursor: 'pointer',
                  }}
                >
                    <FaPlus style={{ marginRight: '0.35rem', verticalAlign: 'middle' }} />
                    Add AWS profile
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={addTab === 'paste'}
                  onClick={() => setAddTab('paste')}
                  style={{
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    borderRadius: 'var(--cs-radius)',
                    border: '1px solid ' + (addTab === 'paste' ? 'var(--cs-primary)' : 'var(--cs-gray-300)'),
                    color: addTab === 'paste' ? '#fff' : 'var(--cs-gray-700)',
                    background: addTab === 'paste' ? 'var(--cs-primary)' : 'var(--cs-gray-50)',
                    cursor: 'pointer',
                  }}
                >
                  <FaPaste style={{ marginRight: '0.35rem', verticalAlign: 'middle' }} />
                  Import by paste
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={addTab === 'role'}
                  onClick={() => setAddTab('role')}
                  style={{
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    borderRadius: 'var(--cs-radius)',
                    border: '1px solid ' + (addTab === 'role' ? 'var(--cs-primary)' : 'var(--cs-gray-300)'),
                    color: addTab === 'role' ? '#fff' : 'var(--cs-gray-700)',
                    background: addTab === 'role' ? 'var(--cs-primary)' : 'var(--cs-gray-50)',
                    cursor: 'pointer',
                  }}
                >
                  <FaUserShield style={{ marginRight: '0.35rem', verticalAlign: 'middle' }} />
                  Set Role
                </button>
              </div>

              {addTab === 'profile' && (
                <div key="panel-profile" style={{ paddingTop: '0.25rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--cs-gray-800)' }}>
                    Add AWS profile
                  </h4>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--cs-gray-500)', marginBottom: '1rem' }}>
                    Enter name, access key, secret key, and region. Optional session token for temporary credentials.
                  </p>
                  <ProfileForm
                    key="add-profile"
                    onSubmit={handleCreate}
                    isLoading={createProfile.isPending}
                    showRoleConfig={false}
                  />
                </div>
              )}
              {addTab === 'role' && (
                <div key="panel-role" data-panel="set-role" style={{ paddingTop: '0.25rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--cs-gray-800)' }}>
                    Set Role — Role configuration only
                  </h4>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--cs-gray-500)', marginBottom: '1rem' }}>
                    Pick an existing profile (its credentials are used) and add a new profile that assumes an AWS role. No access keys here — only <strong>Use existing role</strong> (role name) or <strong>Custom role configuration</strong> (JSON).
                  </p>
                  <SetRoleForm
                    profiles={profiles}
                    onSubmit={handleCreateFromRole}
                    isLoading={createProfileFromRole.isPending}
                  />
                </div>
              )}
              {addTab === 'paste' && (
                <div key="panel-paste" style={{ paddingTop: '0.25rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--cs-gray-800)' }}>
                    Import by paste
                  </h4>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--cs-gray-500)', marginBottom: '0.75rem' }}>
                    Paste from <strong>~/.aws/credentials</strong> (access key, secret) or <strong>~/.aws/config</strong> (role_arn, source_profile). Choose format below.
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      gap: '0.5rem',
                      marginBottom: '1rem',
                      background: 'var(--cs-gray-50)',
                      padding: '0.5rem',
                      borderRadius: 'var(--cs-radius)',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setPasteFormat('credentials')}
                      style={{
                        flex: 1,
                        padding: '0.5rem 0.75rem',
                        fontSize: '0.8125rem',
                        fontWeight: 500,
                        border: '1px solid ' + (pasteFormat === 'credentials' ? 'var(--cs-primary)' : 'var(--cs-gray-300)'),
                        borderRadius: 'var(--cs-radius)',
                        background: pasteFormat === 'credentials' ? 'var(--cs-primary)' : 'white',
                        color: pasteFormat === 'credentials' ? '#fff' : 'var(--cs-gray-700)',
                        cursor: 'pointer',
                      }}
                    >
                      Credentials (~/.aws/credentials)
                    </button>
                    <button
                      type="button"
                      onClick={() => setPasteFormat('config')}
                      style={{
                        flex: 1,
                        padding: '0.5rem 0.75rem',
                        fontSize: '0.8125rem',
                        fontWeight: 500,
                        border: '1px solid ' + (pasteFormat === 'config' ? 'var(--cs-primary)' : 'var(--cs-gray-300)'),
                        borderRadius: 'var(--cs-radius)',
                        background: pasteFormat === 'config' ? 'var(--cs-primary)' : 'white',
                        color: pasteFormat === 'config' ? '#fff' : 'var(--cs-gray-700)',
                        cursor: 'pointer',
                      }}
                    >
                      Config (~/.aws/config)
                    </button>
                  </div>
                  {pasteFormat === 'credentials' ? (
                    <CredentialParser
                      onSubmit={handleParseCredentials}
                      isLoading={parseCredentials.isPending}
                    />
                  ) : (
                    <ConfigParser
                      onSubmit={handleParseConfig}
                      isLoading={parseConfig.isPending}
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        </Col>

        {/* Right box: Existing profiles with subtabs inside */}
        <Col lg={6}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaCheckCircle style={{ color: 'var(--cs-success)' }} />
                Existing Profiles
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    background: 'var(--cs-primary-subtle)',
                    color: 'var(--cs-primary)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '9999px',
                    fontWeight: 500,
                  }}
                >
                  {profiles.length} profiles
                </span>
                <button
                  type="button"
                  className="btn-modern btn-modern-secondary"
                  onClick={() => refetch()}
                  disabled={isRefetching}
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.8125rem' }}
                  title="Refresh list"
                >
                  {isRefetching ? '…' : 'Refresh'}
                </button>
              </span>
            </div>
            <div className="card-body">
              <div
                className="subtab-bar"
                style={{
                  display: 'flex',
                  gap: 0,
                  background: 'var(--cs-gray-100)',
                  padding: '0.25rem',
                  borderRadius: 'var(--cs-radius)',
                  marginBottom: '1rem',
                }}
              >
                <Nav
                  variant="pills"
                  activeKey={listTab}
                  onSelect={(k) => k && setListTab(k as 'all' | 'active')}
                  style={{ display: 'flex', gap: '0.25rem' }}
                >
                  <Nav.Item>
                    <Nav.Link
                      eventKey="all"
                      style={{
                        padding: '0.4rem 0.65rem',
                        fontSize: '0.8125rem',
                        fontWeight: 500,
                        borderRadius: 'var(--cs-radius-sm)',
                        color: listTab === 'all' ? '#fff' : 'var(--cs-gray-600)',
                        background: listTab === 'all' ? 'var(--cs-primary)' : 'transparent',
                      }}
                    >
                      All
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link
                      eventKey="active"
                      style={{
                        padding: '0.4rem 0.65rem',
                        fontSize: '0.8125rem',
                        fontWeight: 500,
                        borderRadius: 'var(--cs-radius-sm)',
                        color: listTab === 'active' ? '#fff' : 'var(--cs-gray-600)',
                        background: listTab === 'active' ? 'var(--cs-primary)' : 'transparent',
                      }}
                    >
                      Active
                    </Nav.Link>
                  </Nav.Item>
                </Nav>
              </div>

              {profiles.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem' }}>
                  <div className="empty-icon">
                    <FaUserCog />
                  </div>
                  <h3>No Profiles Yet</h3>
                  <p style={{ marginBottom: '1rem' }}>Add your first AWS profile in the box on the left using one of these:</p>
                  <ul style={{ textAlign: 'left', maxWidth: '20rem', margin: '0 auto', paddingLeft: '1.5rem', color: 'var(--cs-gray-600)', fontSize: '0.9rem' }}>
                    <li><strong>Add new profile</strong> — Form: name, access key, secret key, region (no role).</li>
                    <li><strong>Import by paste</strong> — Paste <code style={{ fontSize: '0.8rem' }}>~/.aws/credentials</code> or <code style={{ fontSize: '0.8rem' }}>~/.aws/config</code> to add profiles.</li>
                    <li><strong>Set Role</strong> — Add an AWS role (existing or custom) using an existing profile&apos;s credentials.</li>
                  </ul>
                  <p style={{ marginTop: '1rem', fontSize: '0.8125rem', color: 'var(--cs-gray-500)' }}>
                    If you just added or imported a profile, click <strong>Refresh</strong> above to load the list.
                  </p>
                </div>
              ) : (() => {
                const filtered =
                  listTab === 'active' ? profiles.filter((p) => p.is_active) : profiles;
                if (listTab === 'active' && filtered.length === 0) {
                  return (
                    <div className="empty-state" style={{ padding: '1.5rem' }}>
                      <p style={{ margin: 0, color: 'var(--cs-gray-500)' }}>No active profile. Select one and click Set as Active.</p>
                    </div>
                  );
                }
                return (
                  <>
                    {filtered.map((profile) => (
                      <ProfileCard
                        key={profile.id}
                        profile={profile}
                        isActive={selectedId === profile.id || (selectedId == null && profile.is_active)}
                        onSelect={() => setSelectedId(profile.id)}
                        onSetActive={() => {
                          setSelectedId(profile.id);
                          setActiveProfile.mutate(profile.id, {
                            onSuccess: () => notify('Active profile updated', 'success'),
                            onError: (err) => notify(String(err), 'error'),
                          });
                        }}
                        onEdit={() => openEdit(profile)}
                        onDelete={() => handleDelete(profile.id)}
                        deleteConfirm={deleteConfirmId === profile.id}
                      />
                    ))}
                    <p style={{ marginTop: '1rem', fontSize: '0.8125rem', color: 'var(--cs-gray-500)', textAlign: 'center' }}>
                      Select a profile and click <strong>Use</strong> to set it as the active profile for the dashboard.
                    </p>
                  </>
                );
              })()}
            </div>
          </div>
        </Col>
      </Row>

      {/* Edit Modal */}
      <Modal show={editModalShow} onHide={() => setEditModalShow(false)} centered>
        <Modal.Header closeButton style={{ borderBottom: '1px solid var(--cs-gray-200)' }}>
          <Modal.Title style={{ fontWeight: 600 }}>Edit Profile</Modal.Title>
        </Modal.Header>
        <Modal.Body className="form-modern">
          <Form.Group className="mb-3">
            <Form.Label>Custom Name</Form.Label>
            <Form.Control
              value={editCustomName}
              onChange={(e) => setEditCustomName(e.target.value)}
              placeholder="Enter a friendly name for this profile"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>AWS Region</Form.Label>
            <Form.Select value={editRegion} onChange={(e) => setEditRegion(e.target.value)}>
              {['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'].map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer style={{ borderTop: '1px solid var(--cs-gray-200)' }}>
          <button className="btn-modern btn-modern-secondary" onClick={() => setEditModalShow(false)}>
            Cancel
          </button>
          <button
            className="btn-modern btn-modern-primary"
            onClick={handleEditSave}
            disabled={updateProfile.isPending}
          >
            Save Changes
          </button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}
