import { useEffect, useState } from 'react';
import { TopNav } from '../components/TopNav';

interface FreshnessReport {
  last_run: string;
  director_count: number;
  last_verified_30d_percent: number;
  last_verified_90d_percent: number;
  availability_distribution: Record<string, number>;
}

export default function SourcesPage() {
  const [report, setReport] = useState<FreshnessReport | null>(null);

  useEffect(() => {
    fetch('/data/freshness.json')
      .then((response) => response.json())
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>Sources & Freshness</h2>
        <p style={{ color: '#8aa4bf', marginBottom: 12 }}>
          Weekly ingest sources listed in <code>config/sources.yaml</code>.
        </p>
        {report ? (
          <div style={{ fontSize: 12, color: '#b7c7db' }}>
            <p>Last run: {report.last_run}</p>
            <p>Director count: {report.director_count}</p>
            <p>Verified &lt; 30d: {report.last_verified_30d_percent}%</p>
            <p>Verified &lt; 90d: {report.last_verified_90d_percent}%</p>
            <h3 style={{ fontSize: 13, marginTop: 12 }}>Availability distribution</h3>
            <ul>
              {Object.entries(report.availability_distribution).map(([status, count]) => (
                <li key={status}>
                  {status}: {count}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p style={{ color: '#8aa4bf' }}>Freshness report not available.</p>
        )}
      </section>
    </main>
  );
}
