import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { Space, Table, Tag } from 'antd'
import Link from 'next/link'
import Image from 'next/image'
import Layout from '@/components/Layout'
import { API_URL } from '@/config/index'
import styles from '@/styles/Item.module.css'
import { useRouter } from 'next/router'
import { randomUniform } from 'd3'

const { Column, ColumnGroup } = Table

export default function ItemPage ({ item }){
    const router = useRouter();
    const lastUpdated = item.prices//.map((d)=>d.utcTimestamp = new Date(d.utcTimestamp)).sort((a, b)=> a>b)
    console.log(item.prices.slice(0, 5))
    return (
        <Layout>
        <div styles={styles.event}>
            <span>
                {`Last Checked at ${new Date()}`}
            </span>
            <h1>{item.description}</h1>
            <ToastContainer />
            {item.images && (
                <div className={styles.img}>
                    <Image
                        src={'/images/item-default.png'}
                        width={960}
                        height={600}
                    />
                </div>
            )}

            <h3>Brands</h3>
            <p>{item.brand ? item.brand.name : 'Generic'}</p>
            <h3>Description</h3>
            <div dangerouslySetInnerHTML={{__html: item.romanceDescription}}></div>
            <h3>Size: {item.customerFacingSize}</h3>
            <p>Weight: {item.weight.replaceAll(/(_|\[|\])+/g, ' ')}</p>
            <div>
                <Table dataSource={item.prices}>
                <Column title={'Snapshot @'} dataIndex={'utcTimestamp'} key={'utcTimestamp'}></Column>
                <Column title={'Cost ($)'} dataIndex={'value'} key={'value'}></Column>
                <Column title={'Location'} dataIndex={'locationId'} key={'locationId'}></Column>
                <Column
                    title={"Tags"}
                    dataIndex={'type'}
                    key={'type'}
                    render={(type)=>{
                        let color = ''
                        type==='YellowTag'? color='yellow' : color='blue';
                       return (<Tag color={color} key={type}>
                            {type.replace('Tag', ' Tag')} 
                       </Tag>)
                    }}
                    />
                </Table>
            </div>
            
            <Link href='/items'>
                <a className={styles.back}>{'<'} Go Back</a>
            </Link>
        </div>

        </Layout>
    )

}

export async function getServerSideProps({ query: { slug }}) {
    const res = await fetch(`${API_URL}/item?slug=${slug}&collection=items`)
    const item = await res.json()
    item.prices.map((d)=>d.utcTimestamp = String(d.utcTimestamp))
    return {
        props: {
            item: item
        }
    }
}






