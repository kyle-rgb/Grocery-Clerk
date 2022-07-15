import Link from 'next/link'
import Image from 'next/image'
import styles from '@/styles/Item.module.css'

export default function Item ({item}) {

    console.log(item.images)

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

                </div> 
                
            </div>

            <div className={styles.link}></div>
                <Link href={`/item/${item.upc}`}>
                    <a className='btn'>Details</a>
                </Link>
        </div>
    )
  
}
































































