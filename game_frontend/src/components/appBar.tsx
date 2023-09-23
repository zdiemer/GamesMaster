import Link from 'next/link'
import styles from '../styles/components/appBar.module.scss';

export default function AppBar() {
    return (
        <>
            <header className={styles.bar}>
                <div className={styles.verticalContainer}>
                    <Link href='/' className={styles.homeLink}>Home</Link>
                    <div className={styles.title}>Games Master Frontend v0.0.1</div>
                </div>
            </header>
            <div className={styles.spacer}></div>
        </>);
}
