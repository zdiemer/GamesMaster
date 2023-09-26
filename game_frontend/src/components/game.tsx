import styles from '../styles/components/games.module.scss'
import Link from 'next/link'
import { useSWR } from '../lib/fetcher';
import { useState } from 'react';

export function Game({ game }: any) {
    return (
        <div className={styles.game}>
            <h3>
                <Link href={`/games/${game.url_slug}`}>{game.title}</Link>
            </h3>
            <p>{game.modes.join(", ")}</p>
            <p>{game.genres.join(", ")}</p>
            <p>
                Developed by:
                <br />
                {game.developers.join(", ")}
            </p>
        </div>
    );
}

export function GamesListWithPaging({ platform, franchise, developer, publisher }: { platform?: string, franchise?: string, developer?: string, publisher?: string}) {
    const [pageIndex, setPageIndex] = useState(1);
    const query_param_platforms = !!platform ? `&platform=${platform}` : "";
    const query_param_franchise = !!franchise ? `&franchise=${franchise}` : "";
    const query_param_developer = !!developer ? `&developer=${developer}` : "";
    const query_param_publisher = !!publisher ? `&publisher=${publisher}` : "";
    const { data } = useSWR(`/api/games?page=${pageIndex}${query_param_platforms}${query_param_franchise}${query_param_developer}${query_param_publisher}`);

    return (<>
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
    </>);
}

function GameListItem({ game }: any) {
    return (
      <Link href={`/games/${game.url_slug}`}>{game.title}</Link>
    );
  }