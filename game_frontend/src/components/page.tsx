import { ReactNode } from 'react';
import styles from '../styles/components/page.module.scss';

export default function Page({ children }: { children: ReactNode }) {
    return (
    <div className={styles.page}>
        <main>
            {children}
        </main>
    </div>); 
}