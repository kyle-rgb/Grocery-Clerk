import { useRouter } from 'next/router'
import Link from 'next/Link'
import Layout from '@/components/Layout'
import Item from '@/components/Item'
import { API_ROUTE } from '@/config/index'

// import qs from 'qs'

export default function SearchPage({ items }){
  const router = useRouter()

  return (
    <Layout title='Search Results'>
        <Link href='/'>Go Back to Home</Link>
        <h1>Search Results for {router.query.term}</h1>
        {items.length===0 && <h3>No Items to Show</h3>}

        {items.map((item)=>{
            <Item key={item.upc} item={item}></Item>
        })}

    </Layout>
)
}

export async function getServerSideProps(){
    // with qs's regex objects, params = { query: { term } }
    const results = await fetch(`${API_URL}/get_items?type=items`)
    const items = await results.json()

    return {
        props: { items }
    }


}

