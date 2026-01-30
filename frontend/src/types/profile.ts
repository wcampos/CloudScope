export interface Profile {
  id: number;
  name: string;
  custom_name?: string | null;
  aws_region: string;
  account_number?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export type RoleType = 'none' | 'existing' | 'custom';

export interface ProfileFormData {
  name: string;
  custom_name?: string;
  aws_access_key_id: string;
  aws_secret_access_key: string;
  aws_region: string;
  role_type?: RoleType;
  role_name?: string;
  direct_session_token?: string;
  aws_session_token?: string;
}
