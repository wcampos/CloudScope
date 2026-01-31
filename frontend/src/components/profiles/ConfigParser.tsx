import { useState, type FormEvent } from "react";
import { Form } from "react-bootstrap";
import { FaFileImport } from "react-icons/fa";

interface ConfigParserProps {
  onSubmit: (configText: string) => void;
  isLoading?: boolean;
}

export default function ConfigParser({ onSubmit, isLoading }: ConfigParserProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (text.trim()) {
      onSubmit(text.trim());
      setText("");
    }
  };

  return (
    <Form onSubmit={handleSubmit} className="form-modern">
      <Form.Group className="mb-3">
        <Form.Label>~/.aws/config</Form.Label>
        <Form.Control
          as="textarea"
          rows={10}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="[profile name]
role_arn = arn:aws:iam::ACCOUNT:role/ROLE_NAME
source_profile = existing_profile_name
region = us-east-1"
          style={{
            fontFamily: "monospace",
            fontSize: "0.85rem",
            background: "var(--cs-gray-50)",
          }}
          required
        />
        <Form.Text style={{ color: "var(--cs-gray-500)", fontSize: "0.8rem" }}>
          Paste <strong>~/.aws/config</strong> only (not credentials). Each section must have{" "}
          <code>role_arn</code> and <code>source_profile</code>. The <code>source_profile</code>{" "}
          must already exist here — add it first under &quot;Add new profile&quot;, then paste
          config that references it.
        </Form.Text>
      </Form.Group>
      <button
        type="submit"
        className="btn-modern btn-modern-primary"
        disabled={isLoading}
        style={{ width: "100%" }}
      >
        <FaFileImport />
        {isLoading ? "Importing..." : "Import from config"}
      </button>
    </Form>
  );
}
