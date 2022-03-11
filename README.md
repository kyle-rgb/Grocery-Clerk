<h1 style='color: green'>
    <b>Meals, Deals and Automobiles</b>
</h1>
<p>
    In their most recent study, the USDA found that the average American who does the grocery shopping for his or her household spends approximately 174.7 minutes per day on shopping, prepping, and eating. Due to this daily excess of time, I have found it difficult to widen my palate and reduce my food waste for any consistent period of time. Instead, my shopping decisions seem to be curbed by my own (mental) recipe inventory and the current deals at supermarket. And yet, I often find I do not know the full deal offerings available to me as Kroger's promotional blend implements corporate level deals and supplier level deals in separate ways. Some promotions need to be actively loaded to your account while most are matched to the product's UPC. The days of printable coupons seem in the aisle are long gone. As Kroger begins to leverage their vast data ecosystem into more paid offerings, the importance of finding value has never been greater.
</p>

[![Built with Cookiecutter React Django](https://img.shields.io/badge/built%20with-Cookiecutter%20React%20Django-blue)](https://img.shields.io/badge/built%20with-Cookiecutter%20React%20Django-blue)

[![wakatime](https://wakatime.com/badge/github/kyle-rgb/Grocery-Clerk.svg)](https://wakatime.com/badge/github/kyle-rgb/Grocery-Clerk)

# A Virtual Shopper 🛒, Deal Hunter 💸 and Personal Dietitian 👨‍🔬 Wrapped into a Single Application
This Application will Leverage the Kroger API and Recipe data sources Across the Web to Create a Meal Plan, a Shopping List and a Savings Guide in one Integrated Web Based Application via Django, MongoDB, Reactive.js and Docker.

## 🧰 Tools 🧰
<div>
    <img src="https://img.icons8.com/fluency/96/000000/docker.png" style='margin-right: 15px'/>
    <img src="https://img.icons8.com/color/96/000000/django.png"  style='margin-right: 15px'/>
    <img src="https://img.icons8.com/officel/80/000000/react.png"  style='margin-right: 15px'/>
    <img src="https://img.icons8.com/color/96/000000/mongodb.png"  style='margin-right: 15px'/>
    <img src="./frontend/src/static/icons8-python.gif" style="width:80px;height:80px;">


</div>

## Local setup
On your terminal, simply do `docker-compose up --build`, and wait for the containers to build. Eventually, you'll be able to see the index page by going to [http://127.0.0.1/](http://127.0.0.1/)

## Test coverage
To run the tests, check your test coverage, and generate a coverage report:

```
docker-compose run --rm django pytest
```

