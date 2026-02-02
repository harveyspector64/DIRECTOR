import Link from 'next/link';

const links = [
  { href: '/radar', label: 'Radar' },
  { href: '/directors', label: 'Directors' },
  { href: '/actors', label: 'Actors' },
  { href: '/lenses', label: 'Lenses' },
  { href: '/sources', label: 'Sources' }
];

export function TopNav() {
  return (
    <header className="panel" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 20 }}>Director Radar</h1>
          <p style={{ fontSize: 13, color: '#8aa4bf' }}>
            Live map of directors, commitments, and adjacency.
          </p>
        </div>
        <nav style={{ display: 'flex', gap: 16, fontSize: 14 }}>
          {links.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
