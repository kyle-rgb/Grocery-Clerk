import Link from 'next/link'
import Layout from '@/components/Layout'
import Item from '@/components/Item'
import { API_URL, PER_PAGE } from '@/config/index'




export default function Home({ items, page, total }){
  console.log(items)
  return (
      <Layout>
          <h1>Current Items</h1>
          {items.length===0 && <h3>No items to show</h3>}

          {items.map((item)=> (
              <Item key={item.upc} item={item}></Item>
          ))}
          
          <Link href={`/items`}>
                <button className='btn-secondary'>See All Items</button>
          </Link>

      </Layout>
  )
}

export async function getServerSideProps({ query: { page = 1 } }){
  const totalRecords = await fetch(`${API_URL}/items/count`) 
  const total = await totalRecords.json()

  const randStart = Math.floor(Math.random() * total.count - 3)

  const itemRes = await fetch(`${API_URL}/get_items?type=items&limit=3&start=${randStart}`)
  const items = await itemRes.json()

  return {props: { items, page:+page, total }}
}







