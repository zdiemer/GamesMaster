import styles from '../styles/components/games.module.scss'
import Link from 'next/link'


export function Game({ game }: any) {
    return (
        <div className={styles.game}>
            <h3>
                <Link href={`/games/${game.url_slug}`}>{game.title}</Link>
            </h3>
            <p>{game.modes.join(", ")}</p>
            <p>{game.genres.join(", ")}</p>
            <p>
                Developed by:
                <br />
                {game.developers.join(", ")}
            </p>
        </div>
    );
}