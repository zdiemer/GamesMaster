import { useRouter } from 'next/router'
import { useSWR } from '../../lib/fetcher';
import { useState } from 'react';
import Page from '../../components/page';
import { GamesListWithPaging } from '../../components/game';

export default function Games() {
  const router = useRouter()
  const { id } = router.query;
  const { data } = useSWR(`/api/franchises/${id}`);

    return (
      <Page>
      <h1>The {data?.name} Franchise</h1>
      <h2>Games in this franchise</h2>
      <GamesListWithPaging franchise={id}></GamesListWithPaging>
    </Page>);
};