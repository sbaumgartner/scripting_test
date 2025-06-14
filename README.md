# 🧪 Automation Assignment: Playwright + Python – Saucedemo.com

## 📋 Overview

Your task is to build a basic browser automation script using **Playwright in Python** to interact with a public web app: [https://www.saucedemo.com](https://www.saucedemo.com).

This should demonstrate your ability to:

* Navigate and interact with UI elements
* Automate form submissions
* Handle validation errors
* Extract and export structured data
  
We expect you to spend a few hours on this assignment. You're free to spend more time if you’d like. You can start whenever you're ready and do not need to start this today.
You can use any tool(s) or AI you want to complete this assignment.

---

## 🎯 Goals

1. Attempt login with both valid and invalid inputs
2. Capture and log any form validation errors
3. After successful login, extract product names and prices
4. Simulate a checkout attempt with missing data and log validation results
5. Save product data to a `.csv` file
6. Log all major steps and actions taken
7. Extra credit:  Make the automation lookup one specific product (your choice) on the website.  Use a pydantic model that validates the input to ensure only valid input is given the automation and add validation to given clear errors if input is invalid.  Make the input be a json file that is validated by the pydantic model before running the automation.
8. Extra Extra credit:  split the automation into distinct tasks and implement these using Prefect and show them in the Prefect UI. https://github.com/PrefectHQ/prefect.  

---

## ✅ Requirements

### Technical

* Use at least **Python + Playwright** libraries
* Use the built-in `logging` module for logging
* Save logs to a `.log` file
* Save product data to a `.csv` file
* Include a `requirements.txt` file with all dependencies
* Script must be runnable via CLI using: `python main.py`
* Optionally use pydantic and prefect.

---

## 🧪 Testing & Validation

* Include logs at each step, including validation errors
* Capture screenshots when validation errors are triggered *(optional extra credit)*
* Ensure the `.csv` data file is generated and contains accurate, expected content

---

## 📤 Submission Instructions

1. **Fork this repository**
2. Complete your implementation and commit your changes
3. Send us your name and a link to your GitHub repo once you're done to careers@lamarhealth.com

---

## 📂 Deliverables

* `main.py` – your main automation script
* `products.csv` – product data output
* `automation.log` – log of all steps and errors
* `automation_screenshots/` – *(optional)* directory of screenshots
* `README.md` – summary of the project + answers to the reflection questions below
* Link to a video showing the full automation working (in non headless mode) and also how this appears in perfect UI.

---

## 💭 Reflection Questions (Add you answer into your `README.md`)

* What steps did you prioritize first? Why?
  * Because I had not used Python much in a while, my first steps were getting my development environment set up properly, and getting my first login test working.  Luckily, with Cursor, this only took me about 15 minutes.
* How long did you actually spend on the project?
  * Probably between 3 and 4 hours.  The longest stretch was getting Prefect to work, and determining what to do with my failing test case (checking out with no items in cart results in a "success").
* How did you know your automation was working?
  * Being able to watch chrome run through the steps (by adding additional delays initially) was very helpful for determining what was going right and wrong in the earlier portion of the project.  After I trusted the implementation a bit more, it was simple to audit the console and logs after a run to make sure things went smoothly. 
* What would you improve with more time?
  * I liked the pattern I had going with the JSON files being used to run the actual tests.  I could see an implementation of this with different test suites in these JSON files for different uses.  For example, a smoke test of some kind being run on a production system on some kind of schedule, a more robust test set that developers can run locally, and some middle ground that could be incorporated into a CI/CD process to verify different builds/environments.
