import {UserAddOutlined, UserDeleteOutlined } from '@ant-design/icons'

import Link from 'next/link'
import Search from './Search' //
import styles from '@/styles/Header.module.css'

export default function Header() {
    const user = 1
    var loggedIn = true
    const logout = () => {loggedIn=!loggedIn; return loggedIn}

    return (
        <header className={styles.header}>
            <div className={styles.logo}>
                <Link href='/'>
                    <a>Items Catalogue</a>
                </Link>
            </div>

            <Search />

            <nav>
                <ul>
                    <li>
                        <Link href='/items'>
                            <a>Items</a>
                        </Link>
                        <Link href='/promotions'>
                            <a>Promotions</a>
                        </Link>
                    </li>
                    {user ? (
                        <>
                            <li>
                                <Link href='/account/dashboard'>
                                    <a>Dashboard</a>
                                </Link>
                            </li>
                            <li>
                                <button 
                                    onClick={()=> logout()}
                                    className='btn-secondary btn-icon'
                                >
                                    <UserDeleteOutlined /> Logout
                                </button>
                            </li>
                        </>
                    ) : (
                        <>
                            <li>
                                <Link href='account/login'>
                                    <a className='btn-secondary btn-icon'>
                                        <UserAddOutlined /> Login
                                    </a>
                                </Link>
                            </li>
                        </>
                    )}
                </ul>
            </nav>
        </header>
    )  
}
