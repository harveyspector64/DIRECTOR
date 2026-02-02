import { GetStaticPaths, GetStaticProps } from 'next';
import Link from 'next/link';
import { TopNav } from '../../components/TopNav';
import { Actor, BundleData, Director } from '../../lib/types';
import fs from 'fs';
import path from 'path';

interface ActorDetailProps {
  actor: Actor | null;
  directors: Director[];
}

export default function ActorDetail({ actor, directors }: ActorDetailProps) {
  if (!actor) {
    return (
      <main>
        <TopNav />
        <section className="panel">
          <h2>Actor not found</h2>
          <Link href="/actors">Back to actors</Link>
        </section>
      </main>
    );
  }

  return (
    <main>
      <TopNav />
      <section className="panel">
        <h2>{actor.name}</h2>
        <p style={{ color: '#8aa4bf', marginBottom: 12 }}>Recent director adjacency</p>
        <ul style={{ fontSize: 12, color: '#b7c7db' }}>
          {actor.recent_director_edges.map((edge) => (
            <li key={`${edge.director_id}-${edge.film_title}`} style={{ marginBottom: 8 }}>
              {edge.director_name} · {edge.film_title} ({edge.year})
            </li>
          ))}
        </ul>
        <h3 style={{ fontSize: 14, marginTop: 16, marginBottom: 6 }}>Top adjacent directors</h3>
        <ul style={{ fontSize: 12, color: '#b7c7db' }}>
          {actor.adjacency_top.map((edge) => {
            const director = directors.find((item) => item.id === edge.director_id);
            return (
              <li key={edge.director_id} style={{ marginBottom: 6 }}>
                {director ? (
                  <Link href={`/director/${director.id}`}>{director.name}</Link>
                ) : (
                  edge.director_id
                )}{' '}
                · weight {edge.weight.toFixed(2)}
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const bundle = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'bundle.json'), 'utf-8')
  ) as BundleData;
  const paths = bundle.actors.slice(0, 200).map((actor) => ({ params: { id: actor.id } }));
  return { paths, fallback: 'blocking' };
};

export const getStaticProps: GetStaticProps<ActorDetailProps> = async ({ params }) => {
  const bundle = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'bundle.json'), 'utf-8')
  ) as BundleData;
  const actor = bundle.actors.find((item) => item.id === params?.id) ?? null;
  return {
    props: {
      actor,
      directors: bundle.directors
    },
    revalidate: 3600
  };
};
