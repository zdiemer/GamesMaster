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
      {data?.name}
      <GamesListWithPaging platform={id}></GamesListWithPaging>
    </Page>);
};