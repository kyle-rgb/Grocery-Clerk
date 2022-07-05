import Link from 'next/link'
import Image from 'next/image'
import styles from '@/styles/Item.module.css'

export default function Item ({item}) {
    return (
        <div className={styles.item}>
            <div className={styles.img}>
                <Image 
                    src={item.image ? item.image.formats.tumbnail.url :
                        '/images/item-default.png'
                        }
                    width={170}
                    height={180}
                    ></Image>
            </div>
            
            <div className={styles.info}>
                <span>
                    Lasted Checked At {new Date(item.date).toLocaleDateString('en-US')} at {item.time}
                </span>
                <h3>{item.name}</h3>
            </div>

            <div className={styles.link}></div>
                <Link href={`/item/${item.slug}`}>
                    <a className='btn'>Details</a>
                </Link>
        </div>
    )
  
}
































































