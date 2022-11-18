import Link from 'next/link'
import Image from 'next/image'
import styles from '@/styles/Promotions.module.css'


export default function Promotion ({ promo }) {
    console.log('promo', promo)
    let id;
    if (promo.krogerCouponNumber){
        id = promo.krogerCouponNumber
    } else if (promo.mdid){
        id = promo.mdid
    } else {
        id = promo.id
    }

    let start = new Date(promo.startDate+"Z")
    let end = new Date(promo.expirationDate+"Z")
    let length = Math.floor((end-start) / (1000 * 60 * 24 * 24))


    return (
        <div className={styles.item}>
            <div className={styles.img}>
                <img
                    src={promo.image ? promo.image[0].url :
                    '/images/promo-default.png'
                    }
                    width={150}
                    height={150}
                ></img>
            </div>

            <div className={styles.info}>
                <div className={styles.attributes}>
                    <span>
                        <b>ID: {id}</b>
                    </span>
                    <h3>{promo.shortDescription}</h3>
                    <span>Savings to You: ${(+promo.value).toFixed(2)}</span>
                    <br />
                    <span>Started At: {(new Date(promo.startDate+"Z").toLocaleString())}</span>
                    <br />
                    <span>Ended At: {(new Date(promo.expirationDate+"Z").toLocaleString())}</span>
                    <br />
                    <span>Length : {length}</span>
                </div>

            </div>
        </div>
        
    )  
}















