================ Grocery-Shopping ================

[![Built with Cookiecutter React Django](https://img.shields.io/badge/built%20with-Cookiecutter%20React%20Django-blue)](https://img.shields.io/badge/built%20with-Cookiecutter%20React%20Django-blue)

# A Virtual Shopper 🛒, Deal Hunter 💸 and Personal Dietitian 👨‍🔬 Wrapper into a Single Application
This Application will Leverage the Kroger API and Recipe Datasources Across the Web to Create a Meal Plan, a Shopping List and a Savings Guide in one Integrated Web Based Application via Django, MongoDB, Reactive.js and Docker.

## Local setup
On your terminal, simply do `docker-compose up --build`, and wait for the containers to build. Eventually, you'll be able to see the index page by going to `[http://127.0.0.1/](http://127.0.0.1/)`.

## Test coverage
To run the tests, check your test coverage, and generate a coverage report:

```
docker-compose run --rm django pytest
```

