import useSWR from "swr";
import { Game } from '../components/game';
import Page from '../components/page';
import styles from '../styles/pages/home.module.scss';

export default function Games() {
  const fetcher = (...args) => fetch(...args).then((res) => res.json());
  console.log(`port: ${process.env.API_PORT}`);
  const { data, error, isLoading } = useSWR(`/api/games`, fetcher);
  const { data: dlcData } = useSWR(`/api/games?collections_only=True`, fetcher);

  if (error) return <div>Failed to fetch users.</div>;
  // if (isLoading) return <h2>Loading...</h2>;

  let gameList = [];


  if (!isLoading) {
    for (const [i, results] of data.results.entries()) {
      gameList.push(
        <Game game={results} key={i} />
      );
    }
  }

  return (
    <Page>
      <h1>Games</h1>
      <br />
      <div className={styles.container}>
        {data?.results.map((game, i) => {
          return <Game game={game} key={i} />
        })}
      </div>
      <h1>Collections</h1>
      <br />
      <div className={styles.container}>
        {dlcData?.results.map((game, i) => {
          return <Game game={game} key={i} />
        })}
      </div>
    </Page>)
}