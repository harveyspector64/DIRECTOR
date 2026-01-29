import { AvailabilityStatus, LaneFingerprint } from '../lib/types';

interface FilterPanelProps {
  lane: keyof LaneFingerprint | 'all';
  availability: AvailabilityStatus | 'all';
  query: string;
  onLaneChange: (lane: keyof LaneFingerprint | 'all') => void;
  onAvailabilityChange: (availability: AvailabilityStatus | 'all') => void;
  onQueryChange: (value: string) => void;
}

const lanes: Array<keyof LaneFingerprint> = [
  'action',
  'thriller',
  'crime',
  'comedy',
  'horror',
  'scifi',
  'drama',
  'romance',
  'family',
  'animation'
];

const availabilityOptions: Array<AvailabilityStatus> = [
  'HARD_BUSY',
  'SOFT_BUSY',
  'IN_POST',
  'LIKELY_OPEN',
  'UNKNOWN'
];

export function FilterPanel({
  lane,
  availability,
  query,
  onLaneChange,
  onAvailabilityChange,
  onQueryChange
}: FilterPanelProps) {
  return (
    <section className="panel">
      <h2>Filters</h2>
      <label style={{ display: 'block', marginBottom: 12 }}>
        <span style={{ display: 'block', fontSize: 12, color: '#8aa4bf' }}>Search</span>
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search director or actor"
          style={{ width: '100%', padding: 8, marginTop: 6, borderRadius: 8, border: '1px solid #1f2a36', background: '#0b0f14', color: '#e5eef7' }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: 12 }}>
        <span style={{ display: 'block', fontSize: 12, color: '#8aa4bf' }}>Lane</span>
        <select
          value={lane}
          onChange={(event) => onLaneChange(event.target.value as keyof LaneFingerprint | 'all')}
          style={{ width: '100%', padding: 8, marginTop: 6, borderRadius: 8, border: '1px solid #1f2a36', background: '#0b0f14', color: '#e5eef7' }}
        >
          <option value="all">All lanes</option>
          {lanes.map((laneKey) => (
            <option key={laneKey} value={laneKey}>
              {laneKey}
            </option>
          ))}
        </select>
      </label>
      <label style={{ display: 'block' }}>
        <span style={{ display: 'block', fontSize: 12, color: '#8aa4bf' }}>Availability</span>
        <select
          value={availability}
          onChange={(event) => onAvailabilityChange(event.target.value as AvailabilityStatus | 'all')}
          style={{ width: '100%', padding: 8, marginTop: 6, borderRadius: 8, border: '1px solid #1f2a36', background: '#0b0f14', color: '#e5eef7' }}
        >
          <option value="all">All statuses</option>
          {availabilityOptions.map((option) => (
            <option key={option} value={option}>
              {option.replace('_', ' ')}
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}
