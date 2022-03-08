## Consumer Facing Data Sources
[REFERENCES](https://www.programmableweb.com/category/grocery/api)

### Kroger API :: User Story <Shopping Trip 10-14 Days per Week>
- 5000 Calls Per Day
- Available Routes:
    - /Id for ID of customer (5000 Calls Per Day)
    - /Cart allows you to Add an Item to an authenticated customer's cart (5000 Calls Per Day)
    - /Products allows you to search the Kroger product catalog
        - default value returns 10 in a fuzzy search (can change on each request)
        - filter.limit increases products returned
        - filter.start (aka OFFSET) set number of results to skip in the response
        - Additional Valuable Data: Price (both regular and promo); nationalPrice (both regular and promo) for national price of the item;
        Fullfillment Type (Boolean object of {instore, shiptohome, delivery, curbside}); Aisle Locations;
        - You may also search the API via term (for fuzzy match) or previously looked up productID.
            -filters: term (String>=3); locationId (VarChar 8); productId (Char 13-50); brand (String, case-sensitive, pipe-separated); fulfillment (Char 3)
            start (Int 1-1000); limit (Int 1-50);
    - /Locations allow you to search the departments, chains and details in the Kroger Family
        - Use Location Data to Find Closest Available Chain.
- It seems we can get promotional information based off the query for specific items, but may need to interface with client-app to use promotions to drive meal planning and prep.

#### Tasks

- [ ] Scan and Document Current Saved Receipts with Tesseract
- [ ] Create Visualizations to Sum Up Past Purchases (Past Trips)
- [ ] Collect 120 Saved Recipe via Saved Documents and Recipe APIs
- [ ] Breakdown Recipes into Ingredient Parts (and Convert to kgs) and Cooking Windows {long steps}
- [ ] Store in MongoDB
- [ ] Create a Script to See When My Account Makes a Purchase So it Can Restock the Virtual Pantry (and Add More Recipes)
- [ ] Use Recipes and Virtual Pantry to Create Meal Plan Blocks
- [ ] Attach Some Countdown to Used Recipe Documents to Prevent Repeats When Added to a Meal Plan
- [ ] Add Random Option That Can Override a Meal Plan for One Day to Increase Spontaneity
- [ ] Deliver a Client App that Analyzes Past Carts, Meal Plans and Diet Schedules to Streamline Buying and Cooking Processes for the End User.