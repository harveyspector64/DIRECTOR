import Link from 'next/link';
import { TopNav } from '../components/TopNav';

export default function Home() {
  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>Welcome to Director Radar</h2>
        <p style={{ color: '#8aa4bf', marginTop: 8 }}>
          Start with the live radar timeline or jump to director and actor tables.
        </p>
        <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
          <Link className="badge" href="/radar">
            Open Radar
          </Link>
          <Link className="badge" href="/directors">
            Browse Directors
          </Link>
        </div>
      </section>
    </main>
  );
}
