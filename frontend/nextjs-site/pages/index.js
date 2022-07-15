import Link from 'next/link'
import Layout from '@/components/Layout'
import Item from '@/components/Item'




export default function Home({ items }){
  return (
    <Layout>
      <h1>
        Current Items
      </h1>
      {items.length === 0 && <h3>No Current Items to Show</h3>}

      {items.map((item)=> (
        <Item key={item.id} item={item} />
      ))}

      {items.length>0 && (<Link href='/items'><a>View All Items</a></Link>)}
    </Layout>
  )
}

Home.defaultProps = {
  items: [{
    id: 1,
    upc: "0129210112",
    description: 'Raspberries',
    categories: [{name: 'Fruit'}, {name: 'Produce'}]
  }, {
    id: 2,
    upc: "0129210432",
    description: 'BlackBerries',
    categories: [{name: 'Fruit'}, {name: 'Produce'}]
  }]
}


// export async function getStaticProps(){
//   // const res = await fetch(`PLACE API ROUTE HERE`)
//   // const items = await res.json()
//   var items = [{
//     id: 1,
//     date: "2022-07-21",
//     time: "10pm",
//     name: 'Raspberries',
//     link: '/items/raspberries',
//     slug: 'raspberries', 
//   }, {
//     id: 2,
//     date: "2022-07-26",
//     time: "1pm",
//     name: 'Blackberries',
//     link: '/items/blackberries',
//     slug: 'blackberries', 
//   }]

//   return {
//     props: {items},
//     revalidate: 1
//   }
// }








