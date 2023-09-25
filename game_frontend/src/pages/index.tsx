import Page from '../components/page';
import styles from '../styles/pages/home.module.scss';
import Link from 'next/link'
import { useSWR } from '../lib/fetcher';
import { useState } from 'react';

export default function Games() {
  const [pageIndex, setPageIndex] = useState(1);
  const { data } = useSWR(`/api/games?page=${pageIndex}`);

  const franchises = new Set<string>();

  for (let datum of data?.results || []) {
    (datum.franchises as Array<string>).forEach(f => franchises.add(f));
  }

  return (
    <Page>
      <h1>Games</h1>
      <br />
      <div>
        <span>Alphabetical A→Z</span>
      </div>
      <div className={styles.container}>
        {data?.results?.map((game, i) => {
          return <GameListItem game={game} key={i} />
        })}
      </div>
      <button onClick={() => setPageIndex(pageIndex - 1)} disabled={pageIndex > 1 ? false : true}>Previous</button>
      <button onClick={() => setPageIndex(pageIndex + 1)} disabled={!!data?.next ? false : true} >Next</button>
    </Page>)
}

function GameListItem({ game }: any) {
  return (
    <Link href={`/games/${game.url_slug}`}>{game.title}</Link>
  );
}

function FranchiseSelect({ franchises }: { franchises: Array<string> }) {
  return (<>
    <label for="franchise-select">Filter to franchise:</label>
    <select id="franchise-select">
      {franchises.map((franchise: string) => {
        return (<option>{franchise}</option>);
      })}
    </select>
  </>);
}