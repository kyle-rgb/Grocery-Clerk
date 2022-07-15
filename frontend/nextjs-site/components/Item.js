import Link from 'next/link'
import Image from 'next/image'
import styles from '@/styles/Item.module.css'

export default function Item ({item}) {

    return (
        <div className={styles.item}>
            <div className={styles.img}>
                <img
                    src={item.image ? item.image[0].url:
                        '/images/item-default.png'
                        }
                    width={170}
                    height={180}
                ></img>
            </div>
            
            <div className={styles.info}>
                <div className={styles.attributes}>
                <span>
                    <b>UPC: {item.upc}</b>
                </span>
                <h3>{item.description}</h3>
                <span>size: {item.customerFacingSize}</span>

                
                {item.categories && <ul> {item.categories.map((cat) => {
                    return <li>{cat.name}</li>
                })}</ul>}
                

                </div> 
                
            </div>

            <div className={styles.link}></div>
                <Link href={`/items/${item.upc}`}>
                    <a className='btn'>Details</a>
                </Link>
            </div>
    )
  
}
































































