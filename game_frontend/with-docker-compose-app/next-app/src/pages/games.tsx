import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Games.module.css'
import type { InferGetStaticPropsType, GetStaticProps } from 'next'
import useSWR from "swr";
import Link from 'next/link'
import { Component } from 'react';
import { Game } from '../components/game';

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
        <div className={styles.body}>
            <div className={styles.page}>
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
            </div>
        </div>)
}