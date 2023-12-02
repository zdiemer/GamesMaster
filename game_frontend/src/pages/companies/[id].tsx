import { useRouter } from 'next/router'
import { useSWR } from '../../lib/fetcher';
import { useState } from 'react';
import Page from '../../components/page';
import { GamesListWithPaging } from '../../components/game';

export default function Games() {
  const router = useRouter()
  const { id } = router.query;
  const { data } = useSWR(`/api/companies/${id}`);

    return (
      <Page>
      <h1>{data?.name}</h1>
      <h2>Games developed by this company</h2>
      <GamesListWithPaging developer={id}></GamesListWithPaging>
      <h2>Games published by this company</h2>
      <GamesListWithPaging publisher={id}></GamesListWithPaging>
      </Page>);
};