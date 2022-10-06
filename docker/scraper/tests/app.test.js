// globals URL 
const timeout = 15000;
const url = "http://localhost:80"
// setup for tests 
beforeAll(async () => {
    await page.goto(url, {waitUntil: "domcontentloaded"});    
});

describe("Test page title and header", ()=>{
    test("page title", async ()=> {
        var title = await page.$eval("article.md-content__inner.md-typeset > h1", (el)=>el.innerText) ;
        expect(title).toBe("Getting Started")
    }, timeout)
})