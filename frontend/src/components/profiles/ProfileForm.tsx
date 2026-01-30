import { useState, type FormEvent } from 'react';
import { Form } from 'react-bootstrap';
import { FaPlus, FaKey, FaGlobe, FaUserShield } from 'react-icons/fa';
import type { ProfileFormData, RoleType } from '@/types/profile';

const REGIONS = [
  'us-east-1',
  'us-east-2',
  'us-west-1',
  'us-west-2',
  'eu-west-1',
  'eu-central-1',
  'ap-southeast-1',
  'ap-southeast-2',
  'ap-northeast-1',
];

interface ProfileFormProps {
  onSubmit: (data: ProfileFormData) => void;
  isLoading?: boolean;
}

export default function ProfileForm({ onSubmit, isLoading }: ProfileFormProps) {
  const [roleType, setRoleType] = useState<RoleType>('none');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data: ProfileFormData = {
      name: (form.querySelector('#name') as HTMLInputElement).value,
      custom_name: (form.querySelector('#custom_name') as HTMLInputElement)?.value || undefined,
      aws_access_key_id: (form.querySelector('#aws_access_key_id') as HTMLInputElement).value,
      aws_secret_access_key: (form.querySelector('#aws_secret_access_key') as HTMLInputElement).value,
      aws_region: (form.querySelector('#aws_region') as HTMLSelectElement).value,
      role_type: roleType,
      role_name: (form.querySelector('#role_name') as HTMLInputElement)?.value || undefined,
      direct_session_token: (form.querySelector('#direct_session_token') as HTMLInputElement)?.value || undefined,
      aws_session_token: (form.querySelector('#aws_session_token') as HTMLTextAreaElement)?.value || undefined,
    };
    onSubmit(data);
    form.reset();
    setRoleType('none');
  };

  return (
    <Form onSubmit={handleSubmit} className="form-modern">
      <Form.Group className="mb-3">
        <Form.Label>
          <FaKey style={{ marginRight: '0.375rem', color: 'var(--cs-gray-400)' }} />
          Profile Name
        </Form.Label>
        <Form.Control
          id="name"
          name="name"
          placeholder="e.g., production, development"
          required
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>Custom Display Name (Optional)</Form.Label>
        <Form.Control
          id="custom_name"
          name="custom_name"
          placeholder="Friendly name for this profile"
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>AWS Access Key ID</Form.Label>
        <Form.Control
          id="aws_access_key_id"
          name="aws_access_key_id"
          placeholder="AKIA..."
          required
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>AWS Secret Access Key</Form.Label>
        <Form.Control
          id="aws_secret_access_key"
          name="aws_secret_access_key"
          type="password"
          placeholder="Enter your secret key"
          required
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>
          <FaUserShield style={{ marginRight: '0.375rem', color: 'var(--cs-gray-400)' }} />
          Role Configuration
        </Form.Label>
        <div
          style={{
            background: 'var(--cs-gray-50)',
            borderRadius: 'var(--cs-radius)',
            padding: '0.75rem',
          }}
        >
          {(['none', 'existing', 'custom'] as const).map((type) => (
            <Form.Check
              key={type}
              type="radio"
              name="role_type"
              id={`role_${type}`}
              label={
                type === 'none'
                  ? 'No Role (Use Direct Credentials)'
                  : type === 'existing'
                  ? 'Use Existing Role'
                  : 'Custom Role Configuration'
              }
              checked={roleType === type}
              onChange={() => setRoleType(type)}
              style={{ marginBottom: type !== 'custom' ? '0.5rem' : 0 }}
            />
          ))}
        </div>
      </Form.Group>

      {roleType === 'none' && (
        <Form.Group className="mb-3">
          <Form.Label>AWS Session Token (Optional)</Form.Label>
          <Form.Control
            id="direct_session_token"
            name="direct_session_token"
            placeholder="For temporary credentials"
          />
        </Form.Group>
      )}

      {roleType === 'existing' && (
        <Form.Group className="mb-3">
          <Form.Label>Role Name</Form.Label>
          <Form.Control
            id="role_name"
            name="role_name"
            placeholder="e.g., OrganizationAccountAccessRole"
          />
        </Form.Group>
      )}

      {roleType === 'custom' && (
        <Form.Group className="mb-3">
          <Form.Label>Role Configuration (JSON)</Form.Label>
          <Form.Control
            id="aws_session_token"
            name="aws_session_token"
            as="textarea"
            rows={3}
            placeholder='{"RoleArn": "arn:aws:iam::123456789012:role/MyRole", "RoleSessionName": "session"}'
            style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
          />
        </Form.Group>
      )}

      <Form.Group className="mb-4">
        <Form.Label>
          <FaGlobe style={{ marginRight: '0.375rem', color: 'var(--cs-gray-400)' }} />
          AWS Region
        </Form.Label>
        <Form.Select id="aws_region" name="aws_region" required>
          {REGIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </Form.Select>
      </Form.Group>

      <button
        type="submit"
        className="btn-modern btn-modern-primary"
        disabled={isLoading}
        style={{ width: '100%' }}
      >
        <FaPlus />
        {isLoading ? 'Adding Profile...' : 'Add Profile'}
      </button>
    </Form>
  );
}
