import { Director, ProjectEvent } from './types';

export function toCsv(rows: string[][]): string {
  return rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
}

export function buildDirectorExport(directors: Director[], events: ProjectEvent[]) {
  const rows: string[][] = [
    ['director', 'id_line', 'recent_proof', 'availability', 'sources']
  ];
  directors.forEach((director) => {
    const recent = director.recent_features[0];
    const event = events.find((item) => director.current_events.includes(item.id));
    const sources = event?.sources
      .slice(0, 2)
      .map((source) => `${source.outlet} ${source.published_date ?? ''}`.trim())
      .join(' | ') ?? 'n/a';
    rows.push([
      director.name,
      `${director.scale_proxy} ${Object.entries(director.lane_fingerprint)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(([lane]) => lane)
        .join(' / ')}`,
      recent ? `${recent.title} (${recent.year})` : 'n/a',
      `${director.availability.status} (${director.availability.confidence})`,
      sources
    ]);
  });
  return toCsv(rows);
}

export function downloadCsv(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
