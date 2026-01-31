import { useState, type FormEvent } from "react";
import { Form } from "react-bootstrap";
import { FaUserShield, FaKey } from "react-icons/fa";
import type { Profile, ProfileFromRoleData } from "@/types/profile";

type RoleOption = "existing" | "custom";

interface SetRoleFormProps {
  profiles: Profile[];
  onSubmit: (data: ProfileFromRoleData) => void;
  isLoading?: boolean;
}

export default function SetRoleForm({ profiles, onSubmit, isLoading }: SetRoleFormProps) {
  const [roleOption, setRoleOption] = useState<RoleOption>("existing");
  const [sourceId, setSourceId] = useState<string>("");
  const [name, setName] = useState("");
  const [roleName, setRoleName] = useState("");
  const [customJson, setCustomJson] = useState("");

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const sourceProfileId = parseInt(sourceId, 10);
    if (!sourceId || Number.isNaN(sourceProfileId)) return;
    if (!name.trim()) return;
    if (roleOption === "existing" && !roleName.trim()) return;
    if (roleOption === "custom" && !customJson.trim()) return;

    onSubmit({
      source_profile_id: sourceProfileId,
      name: name.trim(),
      role_type: roleOption,
      role_name: roleOption === "existing" ? roleName.trim() : undefined,
      aws_session_token: roleOption === "custom" ? customJson.trim() : undefined,
    });
    setName("");
    setRoleName("");
    setCustomJson("");
  };

  const canSubmit =
    sourceId && name.trim() && (roleOption === "existing" ? roleName.trim() : customJson.trim());

  return (
    <Form onSubmit={handleSubmit} className="form-modern" data-form="set-role">
      <Form.Group className="mb-3">
        <Form.Label>
          <FaKey style={{ marginRight: "0.375rem", color: "var(--cs-gray-400)" }} />
          Source profile
        </Form.Label>
        <Form.Select value={sourceId} onChange={(e) => setSourceId(e.target.value)} required>
          <option value="">Choose a profile (credentials used to assume the role)</option>
          {profiles.map((p) => (
            <option key={p.id} value={String(p.id)}>
              {p.custom_name || p.name} ({p.name})
            </option>
          ))}
        </Form.Select>
        <Form.Text style={{ color: "var(--cs-gray-500)", fontSize: "0.8rem" }}>
          The selected profile&apos;s credentials will be used to assume the role.
        </Form.Text>
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>New profile name</Form.Label>
        <Form.Control
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. prod-role, cross-account"
          required
        />
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>
          <FaUserShield style={{ marginRight: "0.375rem", color: "var(--cs-gray-400)" }} />
          Role type
        </Form.Label>
        <div
          style={{
            background: "var(--cs-gray-50)",
            borderRadius: "var(--cs-radius)",
            padding: "0.75rem",
          }}
        >
          <div style={{ marginBottom: "0.75rem" }}>
            <Form.Check
              type="radio"
              name="role_option"
              id="role_existing"
              label="Use existing role (from AWS)"
              checked={roleOption === "existing"}
              onChange={() => setRoleOption("existing")}
            />
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--cs-gray-600)",
                marginLeft: "1.5rem",
                marginTop: "0.25rem",
              }}
            >
              Assume an IAM role in the same account by role name.
            </div>
          </div>
          <div>
            <Form.Check
              type="radio"
              name="role_option"
              id="role_custom"
              label="Custom role configuration"
              checked={roleOption === "custom"}
              onChange={() => setRoleOption("custom")}
            />
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--cs-gray-600)",
                marginLeft: "1.5rem",
                marginTop: "0.25rem",
              }}
            >
              Assume a role using JSON (RoleArn, RoleSessionName, etc.).
            </div>
          </div>
        </div>
      </Form.Group>

      {roleOption === "existing" && (
        <Form.Group className="mb-3">
          <Form.Label>Role name</Form.Label>
          <Form.Control
            value={roleName}
            onChange={(e) => setRoleName(e.target.value)}
            placeholder="e.g. OrganizationAccountAccessRole"
            required={roleOption === "existing"}
          />
        </Form.Group>
      )}

      {roleOption === "custom" && (
        <Form.Group className="mb-3">
          <Form.Label>Role configuration (JSON)</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            value={customJson}
            onChange={(e) => setCustomJson(e.target.value)}
            placeholder='{"RoleArn": "arn:aws:iam::123456789012:role/MyRole", "RoleSessionName": "session"}'
            style={{ fontFamily: "monospace", fontSize: "0.85rem" }}
            required={roleOption === "custom"}
          />
        </Form.Group>
      )}

      <button
        type="submit"
        className="btn-modern btn-modern-primary"
        disabled={isLoading || !canSubmit}
        style={{ width: "100%" }}
      >
        <FaUserShield />
        {isLoading ? "Adding..." : "Add profile with role"}
      </button>
    </Form>
  );
}
