export type AvailabilityStatus =
  | 'HARD_BUSY'
  | 'SOFT_BUSY'
  | 'IN_POST'
  | 'LIKELY_OPEN'
  | 'UNKNOWN';

export interface LaneFingerprint {
  action: number;
  thriller: number;
  crime: number;
  comedy: number;
  horror: number;
  scifi: number;
  drama: number;
  romance: number;
  family: number;
  animation: number;
}

export interface Director {
  id: string;
  name: string;
  aliases: string[];
  countries?: string[];
  last_feature_directed_year?: number;
  last_feature_released_year?: number;
  recent_features: Array<{
    title: string;
    year: number;
    film_id?: string;
    genres_normalized: string[];
    top_cast: string[];
  }>;
  lane_fingerprint: LaneFingerprint;
  assignment_score: number;
  scale_proxy: 'small' | 'mid' | 'large';
  cast_adjacency_top: Array<{
    actor_id: string;
    actor_name: string;
    weight: number;
    last_worked_year?: number;
  }>;
  availability: {
    status: AvailabilityStatus;
    next_likely_open_window?: { start?: string; end?: string } | null;
    confidence: 'low' | 'med' | 'high';
    last_verified: string;
  };
  current_events: string[];
  data_freshness: {
    last_event_seen?: string;
    last_profile_rebuild: string;
  };
}

export interface Actor {
  id: string;
  name: string;
  recent_director_edges: Array<{
    director_id: string;
    director_name: string;
    film_title: string;
    year: number;
  }>;
  adjacency_top: Array<{
    director_id: string;
    weight: number;
  }>;
}

export interface ProjectEvent {
  id: string;
  director_id: string;
  project_title: string;
  project_type: 'FEATURE' | 'TV' | 'LIMITED' | 'UNKNOWN';
  status:
    | 'IN_TALKS'
    | 'ATTACHED'
    | 'PREP'
    | 'FILMING'
    | 'WRAPPED'
    | 'POST'
    | 'RELEASED'
    | 'UNKNOWN';
  dates?: {
    start?: string;
    end?: string;
  } | null;
  confidence: 'low' | 'med' | 'high';
  last_verified: string;
  sources: Array<{
    url: string;
    outlet: string;
    title: string;
    published_date?: string;
    snippet?: string;
  }>;
}

export interface BundleData {
  directors: Director[];
  actors: Actor[];
  events: ProjectEvent[];
  updated_at: string;
}
