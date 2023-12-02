import { useRouter } from 'next/router'
import { useSWR } from '../../lib/fetcher';
import { useState } from 'react';
import Page from '../../components/page';
import { GamesListWithPaging } from '../../components/game';

export default function Games() {
  const router = useRouter()
  const { id } = router.query;
  const { data } = useSWR(`/api/platforms/${id}`);

    return (
      <Page>
      <h1>{data?.name}</h1>
      <h2>Games on this platform</h2>
      <GamesListWithPaging platform={id}></GamesListWithPaging>
    </Page>);
};