import Head from 'next/head'
import Image from 'next/image'
import styles from '../../styles/pages/games/games.module.css'
import type { InferGetStaticPropsType, GetStaticPaths, GetStaticProps } from 'next'
import { useRouter } from 'next/router'
import useSWR from "swr";
import { release } from 'os'
import Link from 'next/link'
import { Game } from '../../components/game';
import Page from '../../components/page';

export default function Games() {
  const router = useRouter()
  const { id } = router.query;
  console.log(`id: ${id}`);

  const fetcher = (...args) => fetch(...args).then((res) => res.json());
  console.log(`port: ${process.env.API_PORT}`);
  const { data: gameData, error, isLoading } = useSWR(!!id ? `/api/games/${id}` : null, fetcher);
  const { data: releaseData, error: error2, isLoading: isLoading2 } = useSWR(!!id ? `/api/games/${id}/releases` : null, fetcher);

  if (error || error2) return <div>Failed to fetch users.</div>;
  if (isLoading || isLoading2) return <h2>Loading...</h2>;

  let dlcStanza = undefined;
  if (gameData?.dlc.length > 0) {
    dlcStanza = (
      <div>
        <h2>DLC</h2>
          {gameData?.dlc?.map((game: any, index) => {
            return (
              <div key={index}><Game game={game} /></div>
            );
          })}
      </div>
    );
  }

  let collectionStanza = undefined;
  if (gameData?.collectees.length > 0) {
    collectionStanza = (
      <div>
        <h2>Collection Contents</h2>
          {gameData?.collectees?.map((game: any, index) => {
            return (
              <div key={index}><Game game={game} /></div>
            );
          })}
      </div>
    );
  }

  let developersStanza = undefined;
  if (gameData?.notable_developers.length > 0) {
    developersStanza = (
      <div>
      Developers:
      <ul>
      {gameData?.notable_developers?.map((developer: any, i) => {
        return (
          <li key={i}>{developer.role}: {developer.name}</li>
        );
      })}
      </ul>
    </div>
    );
  }

  return (
    <Page>
        <Link href={`/`}>← back</Link>
        <h1>{gameData?.title}</h1>
        {/* // TODO: exterkamp - use real art for the games. */}
        <img src={`/images/${gameData?.cover_art_uuid}`} height={200}></img>
        <div>
          <p>
            Franchise: <span>{gameData?.franchises.join(", ")}</span>
            <br />
            Genre(s): <span>{gameData?.genres.join(", ")}</span>
            <br />
            Developed by: <span>{gameData?.developers.join(", ")}</span>
          </p>
          {!!developersStanza ? developersStanza : ''}
        </div>
        <span>Releases:</span>
        <ul>
          {releaseData?.results.map((release: any, index) => {
            return (
              <li key={index}>Released {release.release_date} in {release.region} for {release.platforms.join(", ")}</li>
            );
          })}
        </ul>

        {!!dlcStanza ? dlcStanza : ''}
        {!!collectionStanza ? collectionStanza : ''}
      </Page>)
}