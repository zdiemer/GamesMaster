import { ReactNode } from 'react';
import styles from '../styles/components/page.module.scss';
import AppBar from './appBar';

export default function Page({ children }: { children: ReactNode }) {
    return (
    <div className={styles.page}>
        <AppBar></AppBar>
        <main className={styles.main}>
            {children}
        </main>
    </div>); 
}