import Head from 'next/head';
import { useRouter } from 'next/router';
import Image from 'next/image';
import Showcase from './Showcase';
import styles from '@/styles/Layout.module.css';
import utilStyles from '@/styles/utils.module.css';
import Link from 'next/link';

export default function Layout({ title, keywords, description, children }) {
    const router = useRouter();
  
    return (
        <div>
            <Head>
                <title>{title}</title>
                <meta name='description' content={description} />
                <meta name='keywords' content={keywords} />
            </Head>
            
            {router.pathname==='/' && <Showcase />}

            <div className={styles.container}>{children}</div>

        </div>
    )
        
}

Layout.defaultProps = {
    title : 'Grocery Clerk | A Distributed Promotion and Sale Brain',
    description: 'Find the latest deals on food, home goods and prepared meals',
    keywords: 'grocery, frugal, mealplanning, coupons'
}
