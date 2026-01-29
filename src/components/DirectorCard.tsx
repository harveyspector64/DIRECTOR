import { Director, ProjectEvent } from '../lib/types';

interface DirectorCardProps {
  director?: Director;
  events: ProjectEvent[];
}

export function DirectorCard({ director, events }: DirectorCardProps) {
  if (!director) {
    return (
      <section className="panel">
        <h2>Director</h2>
        <p style={{ color: '#8aa4bf', fontSize: 14 }}>
          Select a director to see availability, adjacency, and sources.
        </p>
      </section>
    );
  }

  const currentEvents = events.filter((event) => director.current_events.includes(event.id));

  return (
    <section className="panel">
      <h2>{director.name}</h2>
      <p style={{ fontSize: 12, color: '#8aa4bf', marginBottom: 8 }}>
        {director.countries?.join(', ') || 'Global'} · Last feature {director.last_feature_directed_year ?? '—'}
      </p>
      <div style={{ marginBottom: 12 }}>
        <span className="badge">{director.availability.status}</span>
        <span style={{ fontSize: 12, color: '#8aa4bf', marginLeft: 8 }}>
          {director.availability.confidence} confidence · verified {director.availability.last_verified}
        </span>
      </div>
      <h3 style={{ fontSize: 13, marginBottom: 6 }}>Recent features</h3>
      <ul style={{ fontSize: 12, color: '#b7c7db', marginBottom: 12 }}>
        {director.recent_features.slice(0, 3).map((feature) => (
          <li key={`${feature.title}-${feature.year}`}>
            {feature.title} ({feature.year}) · {feature.genres_normalized.join(', ')}
          </li>
        ))}
      </ul>
      <h3 style={{ fontSize: 13, marginBottom: 6 }}>Adjacency (cast)</h3>
      <ul style={{ fontSize: 12, color: '#b7c7db', marginBottom: 12 }}>
        {director.cast_adjacency_top.slice(0, 5).map((actor) => (
          <li key={actor.actor_id}>
            {actor.actor_name} · weight {actor.weight.toFixed(2)}
          </li>
        ))}
      </ul>
      <h3 style={{ fontSize: 13, marginBottom: 6 }}>Current commitments</h3>
      {currentEvents.length === 0 ? (
        <p style={{ fontSize: 12, color: '#8aa4bf' }}>No active events on file.</p>
      ) : (
        <ul style={{ fontSize: 12, color: '#b7c7db' }}>
          {currentEvents.map((event) => (
            <li key={event.id} style={{ marginBottom: 8 }}>
              <strong>{event.project_title}</strong> · {event.status} · {event.confidence}
              <div style={{ color: '#8aa4bf' }}>
                {event.sources[0]?.outlet} · {event.sources[0]?.published_date || 'n/a'}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
