# An eCommerce API built with Flask
Hosted on Heroku at https://gadgehaven.herokuapp.com/
## GadgeHaven

Gadgehaven is an eCommerce web application for gadgets like Laptops and Phones.
This project was inspired by a project on my python hero to mastery course by Angela Yu.
The project was supposed to be a simple online store with a payment system. I intended to go
simple, but I decided to challenge myself and implement a fairly complicated eCommerce API.
I am happy I made this decision because I was able to learn a lot in the process.

## Stack 
Flask(Python), Postgresql, Stripe API for payments
### Features
These are the features of the application:
#### Homepage
1. Returns the products by the two categories: Phones and Laptops
2. Returns the products based on the average rating in descending order
3. Returns the products based on the number of purchases in descending order 
#### Search
1. The search feature returns the closest results to the name of the product, the specs of the product and the category
#### Filter
1. Filter based on Price range and category
#### Cart
1. Add products to cart
2. Remove products from cart
#### Sign up
1. sign up with email address address and other user details
#### Login/Authentication
1. Login with email and Password
#### Forgot Password
1. Sends an email to the user with a link to reset their password
#### User Profile
1. Change Password
2. Edit Profile
3. View previous purchases
4. View user profile
#### Buy product/Payment
1. User must be logged in to be able to purchase product
2. Use stripe payment platform to pay for goods
3. Send a receipt to user's email
#### Admin Operations
1. Add new product
2. Restock Product
3. delete product
4. edit product details
5. View inventory - Sorted by remaining products in descending order
6. Generate inventory report - Generates a csv file of all the products
7. View Sales report
8. Generate sales report - Generates a csv file of all sales made
9. View reviews
10. Delete reviews

## Project Structure
```
+---online_store
|    +---templates
|    |    +---index.html
|    +---_init_.py
|    +---admin_views.py
|    +---cart.py
|    +---errorhandlers.py
|    +---forms.py
|    +---models.py
|    +---payments.py
|    +---queries.py
|    +---users.py
+---MANIFEST.in
+---Procfile
+---README.md
+---config.py
+---data.py
+---requirements.txt
+---run.py
+---setup.py
```
## Starting the project (Development environment)

- [Fork](https://help.github.com/en/articles/fork-a-repo) the project repository and [clone](https://help.github.com/en/articles/cloning-a-repository) your forked repository to your machine. 
- Set up development environment
- Run ``` pip install -r requirements.txt ```
- Edit config file and comment out 'SERVER_NAME'
- set up database
- Run ``` $env:FLASK_APP = "run.py" ```
- Run ``` $env:FLASK_ENV = "development" ```
- Run ``` flask run --reload ```

### API Documentation
Access the API documentation [here](https://documenter.getpostman.com/view/20042182/UzQvsQD2).

