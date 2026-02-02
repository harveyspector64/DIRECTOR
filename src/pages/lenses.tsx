import { TopNav } from '../components/TopNav';

export default function LensesPage() {
  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>Lenses</h2>
        <p style={{ color: '#8aa4bf', marginBottom: 8 }}>
          Configure saved lenses in <code>config/lenses.yaml</code> and rebuild the bundle.
        </p>
        <div className="badge">Lens builder coming soon</div>
      </section>
    </main>
  );
}
