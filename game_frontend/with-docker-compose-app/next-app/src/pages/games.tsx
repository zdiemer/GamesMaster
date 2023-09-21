import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Games.module.css'
import type { InferGetStaticPropsType, GetStaticProps } from 'next'


export const getStaticProps = (async (context) => {
    const res = await fetch('http://backend:8000/api/games')
    const games = await res.json()
    return { props: { games } }
}) satisfies GetStaticProps<{
    games: any
}>

export default function Games({
    games,
}: any) {

    let gameList = [];

    for (let results of games.results) {
        let title = results.title;
        gameList.push(<div className={styles.game}>{title}</div>);
    }

    return (
        <div className={styles.body}>
            <div className={styles.page}>
                Games
                <br />
                <div className={styles.container}>{gameList}</div>
            </div>
        </div>)
}