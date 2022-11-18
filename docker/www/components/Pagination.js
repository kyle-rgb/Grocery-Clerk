import Link from 'next/link'
import {StepBackwardFilled, StepForwardFilled} from '@ant-design/icons'
import { PER_PAGE } from '@/config/index'

export default ({ page, total, collection}) => {
    total = total.count;
    const lastPage = Math.ceil(total / PER_PAGE)
    return (
        <>
            {page > 1 && (
                <Link href={`/${collection}?page=${page-1}`}>
                    <button className='btn-secondary'><StepBackwardFilled />Previous</button>
                </Link>
            )}

            {page<lastPage && (
                <Link href={`/${collection}?page=${page + 1}`}>
                    <button className='btn-secondary'>Next <StepForwardFilled/></button>
                </Link>
            )
            }

            <Link href={`/${collection}?page=${lastPage}`}>
                <button className='btn-secondary'>Last</button>
            </Link>


        </>
    )  
}
