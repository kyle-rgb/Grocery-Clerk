const fs = require('fs')
const js_summary = require('json-summary') 

let targetDirs = ['../../../scripts/requests/server/collections/fooddepot/items', '../../../scripts/requests/server/collections/fooddepot/coupons',
'../../../scripts/requests/server/collections/publix/items', '../../../scripts/requests/server/collections/publix/coupons',
'../../../scripts/requests/server/collections/aldi']

function readAndMove(target){
    let allItems = []
    let files = fs.readdirSync(target, {encoding: 'utf8', withFileTypes: true})
    files = files.filter((d)=> d.isFile())
    for (let file of files){

        data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
        data = JSON.parse(data)
        allItems = allItems.concat(data)
    }
    let summary = JSON.stringify(js_summary.summarize(allItems), null, 4)
    let prefix = target.split('/').slice(-2,-1)[0]
    let type = ''
    
    target.includes('aldi') ? prefix='aldi' : type=target.split('/').slice(-1)[0];

    fs.writeFileSync(`../../../data/${prefix}${type}Summary.json`, summary)
    
    return null

}

readAndMove('../../../scripts/requests/server/collections/publix/items')

// for (let targetDir of targetDirs){
//     readAndMove(target=targetDir)
// }
