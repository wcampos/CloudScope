import { useState } from 'react';
import { Modal, Form, Container, Row, Col } from 'react-bootstrap';
import ProfileForm from '@/components/profiles/ProfileForm';
import ProfileCard from '@/components/profiles/ProfileCard';
import CredentialParser from '@/components/profiles/CredentialParser';
import {
  useProfiles,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
  useSetActiveProfile,
  useParseCredentials,
} from '@/hooks/useProfiles';
import { useNotification } from '@/context/NotificationContext';
import type { Profile, ProfileFormData } from '@/types/profile';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { FaUserCog, FaCheckCircle, FaPlus, FaPaste } from 'react-icons/fa';

export default function ProfilesPage() {
  const { data: profiles = [], isLoading } = useProfiles();
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const deleteProfile = useDeleteProfile();
  const setActiveProfile = useSetActiveProfile();
  const parseCredentials = useParseCredentials();
  const { notify } = useNotification();

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editModalShow, setEditModalShow] = useState(false);
  const [editProfile, setEditProfile] = useState<Profile | null>(null);
  const [editCustomName, setEditCustomName] = useState('');
  const [editRegion, setEditRegion] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const handleCreate = (data: ProfileFormData) => {
    createProfile.mutate(data, {
      onSuccess: () => notify('Profile added successfully', 'success'),
      onError: (err) => notify(String(err), 'error'),
    });
  };

  const handleParse = (text: string) => {
    parseCredentials.mutate(text, {
      onSuccess: () => notify('Credentials parsed successfully', 'success'),
      onError: (err) => notify(String(err), 'error'),
    });
  };

  const handleSetActive = () => {
    if (selectedId == null) {
      notify('Please select a profile first', 'error');
      return;
    }
    setActiveProfile.mutate(selectedId, {
      onSuccess: () => notify('Active profile updated', 'success'),
      onError: (err) => notify(String(err), 'error'),
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
        {/* Left Column - Forms */}
        <Col lg={6}>
          {/* Add Profile Card */}
          <div className="card-modern mb-4">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaPlus style={{ color: 'var(--cs-primary)' }} />
              Add New Profile
            </div>
            <div className="card-body">
              <ProfileForm onSubmit={handleCreate} isLoading={createProfile.isPending} />
            </div>
          </div>

          {/* Parse Credentials Card */}
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaPaste style={{ color: 'var(--cs-primary)' }} />
              Paste AWS Credentials
            </div>
            <div className="card-body">
              <CredentialParser onSubmit={handleParse} isLoading={parseCredentials.isPending} />
            </div>
          </div>
        </Col>

        {/* Right Column - Existing Profiles */}
        <Col lg={6}>
          <div className="card-modern">
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaCheckCircle style={{ color: 'var(--cs-success)' }} />
                Existing Profiles
              </span>
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
            </div>
            <div className="card-body">
              {profiles.length === 0 ? (
                <div className="empty-state" style={{ padding: '2rem' }}>
                  <div className="empty-icon">
                    <FaUserCog />
                  </div>
                  <h3>No Profiles Yet</h3>
                  <p>Add your first AWS profile using the form on the left.</p>
                </div>
              ) : (
                <>
                  {profiles.map((profile) => (
                    <ProfileCard
                      key={profile.id}
                      profile={profile}
                      isActive={selectedId === profile.id || (selectedId == null && profile.is_active)}
                      onSelect={() => setSelectedId(profile.id)}
                      onEdit={() => openEdit(profile)}
                      onDelete={() => handleDelete(profile.id)}
                      deleteConfirm={deleteConfirmId === profile.id}
                    />
                  ))}
                  <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                    <button
                      className="btn-modern btn-modern-primary"
                      onClick={handleSetActive}
                      disabled={setActiveProfile.isPending}
                      style={{ minWidth: '200px' }}
                    >
                      <FaCheckCircle />
                      Set as Active Profile
                    </button>
                  </div>
                </>
              )}
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
