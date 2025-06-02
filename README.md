Solution implemented using FastAPI + PostgreSQL + Docker + Celery for CSV file handling.

I implemented automatic migration for database for both production and test, so only "docker-compose up --build" is required to start the app.

Address to the docs playground in browser: http://localhost:8000/docs#/

Tests run automatically during compose up but in case of a rerun being needed: "docker-compose up test"

Available endpoints:
- [POST] /api/v1/auth/token - needed to receive the auth token required for headers, user: admin, password: secret
- [POST] /api/v1/transactions/upload - used to upload the CSV file for processing
- [GET] /api/v1/transactions - used to get list of transactions with basic pagination options, and filtering by customer and product
- [GET] /api/v1/transactions/{transaction_id} – used to get data on a single transaction
- [GET] /api/v1/reports/customer-summary/{customer_id} – used to get a summary of a customer's transactions, supports getting summary in a given time period
- [GET] /api/v1/reports/product-summary/{product_id} - used to get a summary of transactions containing the given product, supports getting summary in a given time period
- [GET] /api/v1/tasks/{task_id} - used to get results of the celery worker assigned to the file upload, task_id provided by the upload endpoint

What I could have definitely done better:
- authentication, I opted to go for the simplest bearer hardcoded auth as I was running out of time and still had to implement all the tests. in a production setting would definitely not do but serves fine as "existing" security. with more time I would have probably gone for encrypted users stored in the DB.
- error handling, I spent quite a bit of time adding error handling and logging to various parts of the code, but I feel like it's still not quite up to production standards, which I would honestly love to learn more about.
- getting results of the upload, I feel like having an endpoint to get the results is a bit inelegant, but it is a working solution for dealing with the Celery worker
- pagination feels a bit awkward since I was not sure how to implement it from a client need perspective
- tests, since I was running out of time quite badly near the end I had to cut a few corners, otherwise I would have definitely gone for at least 90% coverage on both unit and integration tests and more edge case testing. In general I feel like the tests are too shallow and basic, but I have done a decent bit of manual testing during implementation of the endpoints so at least there's that

What I blame:
The famously beloved courier service DPD for delivering my new PC cooler (that was supposed to get there on wednesday) on friday afternoon, effectively leaving me with no PC access until friday evening when I finally finished replacing it. Oh and also myself I guess, but it's mostly DPD, I promise.
