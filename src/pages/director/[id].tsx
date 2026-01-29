import { GetStaticPaths, GetStaticProps } from 'next';
import Link from 'next/link';
import { TopNav } from '../../components/TopNav';
import { BundleData, Director, ProjectEvent } from '../../lib/types';
import fs from 'fs';
import path from 'path';

interface DirectorDetailProps {
  director: Director | null;
  events: ProjectEvent[];
}

export default function DirectorDetail({ director, events }: DirectorDetailProps) {
  if (!director) {
    return (
      <main>
        <TopNav />
        <section className="panel">
          <h2>Director not found</h2>
          <Link href="/directors">Back to directors</Link>
        </section>
      </main>
    );
  }

  const currentEvents = events.filter((event) => director.current_events.includes(event.id));

  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>{director.name}</h2>
        <p style={{ color: '#8aa4bf', marginBottom: 12 }}>
          Availability: {director.availability.status} · {director.availability.confidence}
        </p>
        <h3 style={{ fontSize: 14, marginBottom: 6 }}>Recent features</h3>
        <ul style={{ fontSize: 12, color: '#b7c7db', marginBottom: 12 }}>
          {director.recent_features.map((feature) => (
            <li key={`${feature.title}-${feature.year}`}>
              {feature.title} ({feature.year}) · {feature.genres_normalized.join(', ')}
            </li>
          ))}
        </ul>
        <h3 style={{ fontSize: 14, marginBottom: 6 }}>Current events</h3>
        {currentEvents.length === 0 ? (
          <p style={{ fontSize: 12, color: '#8aa4bf' }}>No events listed.</p>
        ) : (
          <ul style={{ fontSize: 12, color: '#b7c7db' }}>
            {currentEvents.map((event) => (
              <li key={event.id} style={{ marginBottom: 8 }}>
                <strong>{event.project_title}</strong> · {event.status}
                <div style={{ color: '#8aa4bf' }}>{event.sources[0]?.url}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const bundle = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'bundle.json'), 'utf-8')
  ) as BundleData;
  const paths = bundle.directors.slice(0, 200).map((director) => ({ params: { id: director.id } }));
  return { paths, fallback: 'blocking' };
};

export const getStaticProps: GetStaticProps<DirectorDetailProps> = async ({ params }) => {
  const bundle = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'bundle.json'), 'utf-8')
  ) as BundleData;
  const director = bundle.directors.find((item) => item.id === params?.id) ?? null;
  return {
    props: {
      director,
      events: bundle.events
    },
    revalidate: 3600
  };
};
