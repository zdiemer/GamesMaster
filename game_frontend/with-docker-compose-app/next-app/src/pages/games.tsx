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
        gameList.push(
            <div className={styles.game}>
                <h2>{results.title}</h2>
                <p>{results.modes.join(", ")}</p>
                <p>{results.genres.join(", ")}</p>
                <p>
                    Developed by:
                    <br/>
                    {results.developers.join(", ")}
                </p>
            </div>);
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