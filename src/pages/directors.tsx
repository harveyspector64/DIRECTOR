import { useEffect, useMemo, useState } from 'react';
import Fuse from 'fuse.js';
import { TopNav } from '../components/TopNav';
import { loadBundle } from '../lib/data';
import { buildDirectorExport, downloadCsv } from '../lib/export';
import { BundleData, Director } from '../lib/types';

export default function DirectorsPage() {
  const [bundle, setBundle] = useState<BundleData | null>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    loadBundle().then(setBundle).catch(() => setBundle(null));
  }, []);

  const fuse = useMemo(() => {
    if (!bundle) {
      return null;
    }
    return new Fuse(bundle.directors, { keys: ['name', 'aliases'], threshold: 0.3 });
  }, [bundle]);

  const filtered = useMemo(() => {
    if (!bundle) {
      return [] as Director[];
    }
    if (!query.trim() || !fuse) {
      return bundle.directors.slice(0, 300);
    }
    return fuse.search(query.trim()).map((result) => result.item).slice(0, 300);
  }, [bundle, query, fuse]);

  return (
    <main>
      <TopNav />
      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Directors</h2>
            <p style={{ color: '#8aa4bf', fontSize: 13 }}>
              Export call grids or browse with live search.
            </p>
          </div>
          <button
            type="button"
            className="badge"
            onClick={() => {
              if (!bundle) {
                return;
              }
              const csv = buildDirectorExport(filtered, bundle.events);
              downloadCsv('director-call-grid.csv', csv);
            }}
          >
            Export CSV
          </button>
        </div>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search directors"
          style={{ width: '100%', padding: 8, margin: '16px 0', borderRadius: 8, border: '1px solid #1f2a36', background: '#0b0f14', color: '#e5eef7' }}
        />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead style={{ textAlign: 'left', color: '#8aa4bf' }}>
              <tr>
                <th>Name</th>
                <th>Lane</th>
                <th>Last Feature</th>
                <th>Availability</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((director) => (
                <tr key={director.id} style={{ borderTop: '1px solid #1f2a36' }}>
                  <td style={{ padding: '8px 0' }}>{director.name}</td>
                  <td>
                    {Object.entries(director.lane_fingerprint)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 2)
                      .map(([lane]) => lane)
                      .join(', ')}
                  </td>
                  <td>{director.last_feature_directed_year ?? '—'}</td>
                  <td>{director.availability.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
