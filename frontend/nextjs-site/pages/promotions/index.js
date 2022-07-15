import Layout from '@/components/Layout'
import Promotion from '@/components/Promotion'
import Pagination from '@/components/Pagination'
import { API_URL, PER_PAGE } from '@/config/index'

export default function PromotionsPage({promotions, page, total}){
    console.log('promotions', promotions)

    return (
        <Layout>
            <h1>Current Promotions</h1>
            {promotions.length===0 && <h3>No promotions to show right now</h3>}

            {promotions.map((promo)=>(
                <Promotion key={promo.krogerCouponNumber} promo={promo}></Promotion>
            ))}

            <Pagination page={page} total={total} collection={'promotions'}/>
        </Layout>
    )  
}

export async function getServerSideProps ({ query: {page = 1} }){
    const start = +page === 1 ? 0 : (+page-1) * PER_PAGE;
    
    const totalRecords = await fetch(`${API_URL}/promotions/count`)
    const total = await totalRecords.json()

    const res = await fetch(`${API_URL}/get_items?type=promotions&limit=${PER_PAGE}&start=${start}`)
    const promotions = await res.json()

    return {
        props: {
            promotions,
            page: +page,
            total
        }
    }



}

