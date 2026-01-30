import { useState, type FormEvent } from 'react';
import { Form } from 'react-bootstrap';
import { FaFileImport } from 'react-icons/fa';

interface CredentialParserProps {
  onSubmit: (credentialsText: string) => void;
  isLoading?: boolean;
}

export default function CredentialParser({ onSubmit, isLoading }: CredentialParserProps) {
  const [text, setText] = useState('');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (text.trim()) {
      onSubmit(text.trim());
      setText('');
    }
  };

  return (
    <Form onSubmit={handleSubmit} className="form-modern">
      <Form.Group className="mb-3">
        <Form.Label>AWS Credentials</Form.Label>
        <Form.Control
          as="textarea"
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={`[profile_name]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
region = us-east-1`}
          style={{
            fontFamily: 'monospace',
            fontSize: '0.85rem',
            background: 'var(--cs-gray-50)',
          }}
          required
        />
        <Form.Text style={{ color: 'var(--cs-gray-500)', fontSize: '0.8rem' }}>
          Paste credentials in ~/.aws/credentials format. Include the profile name in square brackets.
        </Form.Text>
      </Form.Group>
      <button
        type="submit"
        className="btn-modern btn-modern-primary"
        disabled={isLoading}
        style={{ width: '100%' }}
      >
        <FaFileImport />
        {isLoading ? 'Parsing...' : 'Import Credentials'}
      </button>
    </Form>
  );
}
