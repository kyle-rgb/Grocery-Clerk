import Head from 'next/head';
import { useRouter } from 'next/router';
import Image from 'next/image';
import Showcase from './Showcase';
import styles from '@/styles/Layout.module.css';
import Header from './Header'
import Footer from './Footer'

export default function Layout({ title, keywords, description, children }) {
    const router = useRouter();
  
    return (
        <div>
            <Head>
                <title>{title}</title>
                <meta name='description' content={description} />
                <meta name='keywords' content={keywords} />
            </Head>
            
            <Header />
            {router.pathname==='/' && <Showcase />}

            <div className={styles.container}>{children}</div>

            <Footer />
        </div>
    )
        
}

Layout.defaultProps = {
    title : 'Grocery Clerk | A Distributed Promotion and Sale Brain',
    description: 'Find the latest deals on food, home goods and prepared meals',
    keywords: 'grocery, frugal, mealplanning, coupons'
}
