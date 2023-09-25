import Page from '../components/page';
import { useSWR } from '../lib/fetcher';
import { useState } from 'react';
import { GamesListWithPaging } from '../components/game';

export default function Games() {
  const [pageIndex, setPageIndex] = useState(1);
  const { data } = useSWR(`/api/games?page=${pageIndex}`);

  return (
    <Page>
      <h1>Games</h1>
      <br />
      <GamesListWithPaging></GamesListWithPaging>
    </Page>)
}
