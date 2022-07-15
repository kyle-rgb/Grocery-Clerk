import Link from 'next/link'
import { PER_PAGE } from '@/config/index'

export default ({ page, total}) => {
    const lastPage = Math.ceil(total / PER_PAGE)
    return (
        <>
            {page >= 1 && (
                <Link href={`/items?page=${page-1}`}>
                    <a className='btn-secondary'>Previous</a>
                </Link>
            )}

            {page<lastPage && (
                <Link href={`/items?page=${page + 1}`}>
                    <a className='btn-secondary'>Next</a>
                </Link>
            )
            }
        </>
    )  
}
