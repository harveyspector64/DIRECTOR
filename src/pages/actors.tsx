import { useEffect, useMemo, useState } from 'react';
import Fuse from 'fuse.js';
import Link from 'next/link';
import { TopNav } from '../components/TopNav';
import { loadBundle } from '../lib/data';
import { Actor, BundleData } from '../lib/types';

export default function ActorsPage() {
  const [bundle, setBundle] = useState<BundleData | null>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    loadBundle().then(setBundle).catch(() => setBundle(null));
  }, []);

  const fuse = useMemo(() => {
    if (!bundle) {
      return null;
    }
    return new Fuse(bundle.actors, { keys: ['name'], threshold: 0.3 });
  }, [bundle]);

  const filtered = useMemo(() => {
    if (!bundle) {
      return [] as Actor[];
    }
    if (!query.trim() || !fuse) {
      return bundle.actors.slice(0, 300);
    }
    return fuse.search(query.trim()).map((result) => result.item).slice(0, 300);
  }, [bundle, query, fuse]);

  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>Actors</h2>
        <p style={{ color: '#8aa4bf', fontSize: 13 }}>
          Use an actor to find adjacent directors quickly.
        </p>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search actors"
          style={{ width: '100%', padding: 8, margin: '16px 0', borderRadius: 8, border: '1px solid #1f2a36', background: '#0b0f14', color: '#e5eef7' }}
        />
        <ul style={{ fontSize: 12, color: '#b7c7db' }}>
          {filtered.map((actor) => (
            <li key={actor.id} style={{ marginBottom: 8 }}>
              <Link href={`/actor/${actor.id}`}>{actor.name}</Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
