import { useEffect, useMemo, useState } from 'react';
import Fuse from 'fuse.js';
import { FilterPanel } from '../components/FilterPanel';
import { DirectorCard } from '../components/DirectorCard';
import { DirectorTimeline } from '../components/DirectorTimeline';
import { TopNav } from '../components/TopNav';
import { loadBundle } from '../lib/data';
import { AvailabilityStatus, BundleData, Director, LaneFingerprint } from '../lib/types';

export default function RadarPage() {
  const [bundle, setBundle] = useState<BundleData | null>(null);
  const [lane, setLane] = useState<keyof LaneFingerprint | 'all'>('all');
  const [availability, setAvailability] = useState<AvailabilityStatus | 'all'>('all');
  const [query, setQuery] = useState('');
  const [selectedDirectorId, setSelectedDirectorId] = useState<string | null>(null);

  useEffect(() => {
    loadBundle().then(setBundle).catch(() => setBundle(null));
  }, []);

  const fuse = useMemo(() => {
    if (!bundle) {
      return null;
    }
    return new Fuse(bundle.directors, {
      keys: ['name', 'aliases', 'recent_features.title', 'cast_adjacency_top.actor_name'],
      threshold: 0.3
    });
  }, [bundle]);

  const filteredDirectors = useMemo(() => {
    if (!bundle) {
      return [] as Director[];
    }
    let list = bundle.directors;
    if (lane !== 'all') {
      list = list.filter((director) => director.lane_fingerprint[lane] >= 0.4);
    }
    if (availability !== 'all') {
      list = list.filter((director) => director.availability.status === availability);
    }
    if (query.trim() && fuse) {
      list = fuse.search(query.trim()).map((result) => result.item);
    }
    return list.slice(0, 500);
  }, [bundle, lane, availability, query, fuse]);

  const selectedDirector = useMemo(() => {
    if (!bundle || !selectedDirectorId) {
      return undefined;
    }
    return bundle.directors.find((director) => director.id === selectedDirectorId);
  }, [bundle, selectedDirectorId]);

  return (
    <main>
      <TopNav />
      <div className="layout">
        <FilterPanel
          lane={lane}
          availability={availability}
          query={query}
          onLaneChange={setLane}
          onAvailabilityChange={setAvailability}
          onQueryChange={setQuery}
        />
        <section className="panel">
          <h2>Timeline</h2>
          {bundle ? (
            <DirectorTimeline
              directors={filteredDirectors}
              events={bundle.events}
              onSelectDirector={setSelectedDirectorId}
            />
          ) : (
            <p style={{ color: '#8aa4bf' }}>Loading bundle...</p>
          )}
        </section>
        <DirectorCard director={selectedDirector} events={bundle?.events ?? []} />
      </div>
    </main>
  );
}
