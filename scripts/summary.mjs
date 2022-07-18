import {readdir, readFile} from 'fs';


let targetDir = './requests/server/collections/fooddepot/items'

let allItems = []

readdir(targetDir, (err, files)=>{
    if (err) throw err
    for (let file of files){
        readFile(targetDir+"/"+file, 'utf8', (err, data)=>{
            if (err) throw err
            data = JSON.parse(data)
            console.log(targetDir+'/'+file, data.length)
            allItems = allItems.concat(data)
            console.log('allItemsSize', allItems.length)
        })
    }
    
})
