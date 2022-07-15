const http = require('http')

result = http.get({hostname: 'localhost', port: 5000, path: '/i', agent: false}, (res)=>{
    
    res.on('data', (d)=>{
        process.stdout.write(d)
    })
})
