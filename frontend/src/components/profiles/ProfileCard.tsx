import { FaEdit, FaTrash, FaCheckCircle } from 'react-icons/fa';
import type { Profile } from '@/types/profile';

interface ProfileCardProps {
  profile: Profile;
  isActive: boolean;
  onSelect: () => void;
  onSetActive: () => void;
  onEdit: () => void;
  onDelete: () => void;
  deleteConfirm?: boolean;
}

export default function ProfileCard({
  profile,
  isActive,
  onSelect,
  onSetActive,
  onEdit,
  onDelete,
  deleteConfirm,
}: ProfileCardProps) {
  return (
    <div
      className={`profile-card ${isActive ? 'selected' : ''}`}
      onClick={onSelect}
      style={{ cursor: 'pointer' }}
    >
      <div className="profile-header">
        <input
          type="radio"
          name="profile_id"
          id={`profile_${profile.id}`}
          value={profile.id}
          checked={isActive}
          onChange={onSelect}
          className="profile-radio"
          onClick={(e) => e.stopPropagation()}
          style={{ width: '18px', height: '18px', accentColor: 'var(--cs-primary)' }}
        />
        <div className="profile-info">
          <div className="profile-name">
            {profile.custom_name || profile.name}
            {profile.custom_name && (
              <small> ({profile.name})</small>
            )}
            {profile.is_active && (
              <FaCheckCircle
                style={{ marginLeft: '0.5rem', color: 'var(--cs-success)', fontSize: '0.9rem' }}
                title="Currently active"
              />
            )}
          </div>
          <div className="profile-meta">
            {profile.account_number && (
              <span>Account: {profile.account_number} &bull; </span>
            )}
            Region: {profile.aws_region}
          </div>
        </div>
      </div>
      <div className="profile-actions">
        <button
          type="button"
          className={`btn-modern ${isActive ? 'btn-modern-primary' : 'btn-modern-outline'}`}
          onClick={(e) => {
            e.stopPropagation();
            onSetActive();
          }}
          style={{
            padding: '0.4rem 0.75rem',
            fontSize: '0.8rem',
            ...(isActive ? { cursor: 'default' as const } : {}),
          }}
          title={isActive ? 'Currently in use' : 'Use this profile'}
        >
          <FaCheckCircle />
          {isActive ? 'In use' : 'Use'}
        </button>
        <button
          type="button"
          className="btn-modern btn-modern-outline"
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
          style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
        >
          <FaEdit />
          Edit
        </button>
        <button
          type="button"
          className={`btn-modern ${deleteConfirm ? 'btn-modern-primary' : 'btn-modern-outline'}`}
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          style={{
            padding: '0.4rem 0.75rem',
            fontSize: '0.8rem',
            background: deleteConfirm ? 'var(--cs-danger)' : undefined,
            borderColor: deleteConfirm ? 'var(--cs-danger)' : undefined,
            color: deleteConfirm ? 'white' : undefined,
          }}
        >
          <FaTrash />
          {deleteConfirm ? 'Confirm Delete' : 'Delete'}
        </button>
      </div>
    </div>
  );
}
