export const API_URL = 'http://localhost:8000/api/v1';

export interface User {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
}

export interface Family {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Album {
  id: number;
  family_id: number;
  name: string;
  visibility: string;
  created_at: string;
  updated_at: string;
}

export interface Media {
  id: number;
  album_id: number;
  resource_type: string;
  format: string;
  bytes: number;
  width: number | null;
  height: number | null;
  duration: number | null;
  original_filename: string;
  created_at: string;
  url: string;
  thumbnail_url: string;
  download_url: string;
}

export interface MediaListResponse {
  items: Media[];
  total: number;
  page: number;
  page_size: number;
}
