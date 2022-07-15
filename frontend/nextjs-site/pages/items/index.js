import Layout from '@/components/Layout'
import Item from '@/components/Item'
import Pagination from '@/components/Pagination'
import { API_URL, PER_PAGE } from '@/config/index'

export default function ItemsPage({ items, page, total }){
    return (
        <Layout>
            <h1>Current Items</h1>
            {items.length===0 && <h3>No items to show</h3>}

            {items.map((item)=> (
                <Item key={item.upc} item={item}></Item>
            ))}
            
            <Pagination page={page} total={total} />
        </Layout>
    )
}

export async function getServerSideProps({ query: { page = 1 } }){
    const start = +page === 1 ? 0 : (+page-1) * PER_PAGE;

    const totalRecords = await fetch(`${API_URL}/items/count`) 
    const total = await totalRecords.json()

    const itemRes = await fetch(`${API_URL}/items?limit=${PER_PAGE}&start=${start}`)
    const items = await itemRes.json()

    return {props: { items, page:+page, total }}
} 
