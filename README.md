# 💸 SpendSettle

### Track. Split. Settle.

**SpendSettle** is a full-stack personal finance and shared-expense management web application built with **Flask, Python, MongoDB Atlas, HTML, CSS, and JavaScript**.

The project started as a small **Object-Oriented Programming project**, but instead of keeping it as a basic console or GUI application, I decided to evolve it into a complete web product with a backend, responsive frontend, cloud database, authentication, deployment pipeline, and real-world financial features.

🌐 **Live Application:**  
https://spendsettle.onrender.com

💻 **Source Code:**  
https://github.com/MarwanElbarbary/SpendSettle

---

## 🚀 Project Story

SpendSettle did not start as a full web application.

The original idea was a relatively small **Digital Wallet OOP project** designed to demonstrate concepts such as:

- Encapsulation
- Inheritance
- Polymorphism
- Composition
- Classes and Objects

Instead of stopping after implementing the required functionality, I decided to approach the project differently.

I wanted to answer a bigger question:

> **What would this project look like if it were treated as a real product instead of just an assignment?**

From there, the project gradually evolved from a simple wallet system into a complete financial management platform.

The development journey became:

```text
Basic OOP Project
        ↓
Digital Wallet Logic
        ↓
Database Integration
        ↓
Flask Backend
        ↓
Responsive Web Interface
        ↓
Authentication & Security
        ↓
Personal Finance Tracking
        ↓
Shared Expenses & Bill Splitting
        ↓
Cloud Database
        ↓
Production Deployment
        ↓
SpendSettle
```

This evolution represents one of the main goals behind the project:

> **Not only completing a task, but thinking about how a simple idea can become a complete, usable software product.**

---

# ✨ Main Features

## 👤 Authentication

SpendSettle includes a complete user authentication flow.

Users can:

- Create an account
- Sign in securely
- Sign out
- Access their personal dashboard
- Manage their account information
- Change their wallet PIN

Each user's financial information is isolated from other users.

---

## 💳 Digital Wallet

The wallet is one of the core parts of SpendSettle.

Users can:

- Deposit money
- Withdraw money
- Transfer money to other SpendSettle users
- Make wallet payments
- Make card payments
- View transaction history
- View transaction receipts

The wallet also provides monthly activity statistics such as:

- Money In
- Money Out
- Number of transactions

---

## 🔐 PIN-Protected Balance

The wallet balance is hidden by default.

Instead of sending the balance directly to the frontend, the user must verify their PIN before the backend exposes the balance.

```text
User opens wallet
       ↓
Balance is hidden
       ↓
User enters PIN
       ↓
Backend verifies PIN
       ↓
Balance becomes visible
```

The user can also hide the balance again at any time.

This feature was implemented to improve privacy when the application is being used around other people.

---

# 📊 Personal Finance — My Money

SpendSettle is not only a wallet.

It also helps users understand and manage their personal spending.

Users can:

- Add personal expenses
- Categorize expenses
- Add expense notes
- Set a monthly budget
- Track total monthly spending
- See remaining budget
- Monitor budget progress

Example:

```text
Monthly Budget: 10,000 EGP

Spent:           6,250 EGP
Remaining:       3,750 EGP
Progress:        62.5%
```

---

## 📅 Monthly Finance History

Financial tracking is organized by month.

Users can review previous months and see their historical:

- Expenses
- Budgets
- Spending activity

This allows SpendSettle to work as an ongoing personal finance system rather than only displaying the current month.

---

# 👥 Shared Expenses & Bill Splitting

SpendSettle includes a complete shared expense management system.

Users can create groups for situations such as:

- Trips
- Roommates
- Friends
- Family expenses
- Events
- Shared subscriptions
- Group purchases

---

## 🏠 Groups

Users can:

- Create groups
- Add members
- Rename groups
- Archive groups
- Restore archived groups
- Delete groups

Each group contains its own:

- Members
- Expenses
- Settlements
- Balances

---

## 🧾 Shared Expenses

Members can add expenses inside a group.

SpendSettle supports multiple splitting methods.

### Equal Split

Example:

```text
Bill = 900 EGP
Members = 3

Each member owes:

300 EGP
```

### Exact Amount Split

Users can manually specify exactly how much each participant owes.

Example:

```text
Total = 1,000 EGP

Ahmed  → 500 EGP
Marwan → 300 EGP
Omar   → 200 EGP
```

### Percentage Split

Expenses can also be divided using percentages.

Example:

```text
Ahmed  → 50%
Marwan → 30%
Omar   → 20%
```

The system calculates every participant's financial position automatically.

---

# 🤝 Debt Settlement

SpendSettle calculates balances between group members.

For each group, the application determines:

```text
Who owes money?
Who should receive money?
How much should be paid?
```

A user who owes another group member can settle the debt directly using their SpendSettle wallet.

The payment updates:

- Wallet balances
- Group settlements
- Group balances
- Transaction records

This connects the **Wallet System** with the **Shared Expense System** instead of keeping them as separate features.

---

# 🧾 Transaction Receipts

Wallet operations generate transaction records that users can review later.

Receipt information can include:

- Transaction ID
- Transaction type
- Amount
- Date
- Description
- Status

This helps maintain a clear financial activity history.

---

# 🏠 Overview Dashboard

The SpendSettle dashboard provides a quick overview of the user's financial activity.

It includes information such as:

### Wallet

- Current balance
- Money in
- Money out

### Personal Finance

- Monthly budget
- Amount spent
- Remaining budget

### Shared Money

- Money you owe
- Money others owe you
- Number of active groups

### Quick Actions

Users can quickly:

- Send money
- Add an expense
- Split a bill
- Create a group

---

# 🎨 User Interface

SpendSettle uses a custom responsive FinTech-inspired interface.

The design focuses on:

- Clean layouts
- Clear financial information
- Simple navigation
- Responsive pages
- Consistent components
- Minimal visual clutter

Main navigation:

```text
SpendSettle

Overview
Wallet
Money
Groups
Profile
```

The visual identity follows a modern FinTech style using:

- Deep Navy / Ink
- Electric Indigo
- Emerald accents

---

# 🏗️ System Architecture

```mermaid
flowchart TD

    USER[User Browser]

    FLASK[Flask Application]

    AUTH[Authentication Service]
    WALLET[Wallet Service]
    FINANCE[Finance Service]
    GROUPS[Shared Expense Service]

    DB[Database Manager]

    ATLAS[(MongoDB Atlas)]

    USER --> FLASK

    FLASK --> AUTH
    FLASK --> WALLET
    FLASK --> FINANCE
    FLASK --> GROUPS

    AUTH --> DB
    WALLET --> DB
    FINANCE --> DB
    GROUPS --> DB

    DB --> ATLAS
```

---

# 🧠 OOP Design

The project keeps Object-Oriented Programming principles at its core.

## Encapsulation

Financial and security-related operations are handled through dedicated classes and services instead of directly modifying application data everywhere.

---

## Inheritance & Polymorphism

Payment methods use a shared abstraction with different implementations.

```text
PaymentMethod
     │
     ├── WalletPayment
     │
     └── CardPayment
```

Each payment method can implement its own payment behavior while sharing the same general interface.

---

## Composition

Objects such as users, wallets, transactions, groups, and expenses work together to build larger application features.

---

# 🧩 Backend Architecture

The backend follows a service-based architecture.

```text
Flask Routes
     ↓
Service Layer
     ↓
Database Manager
     ↓
MongoDB Atlas
```

This prevents large amounts of business logic from being placed directly inside routes.

Main services include:

```text
AuthService
WalletService
FinanceService
SharedExpenseService
SecurityManager
```

---

# 🗄️ Database

SpendSettle uses **MongoDB Atlas** as its cloud database.

Main collections include:

```text
users

transactions

expenses

budgets

groups

group_expenses

group_settlements
```

Several database indexes are also used for fields such as:

- Username
- Transaction ID
- Expense ID
- Group ID
- Settlement ID
- User and date combinations

---

# 🛠️ Tech Stack

## Backend

- Python
- Flask
- Gunicorn
- PyMongo

## Database

- MongoDB
- MongoDB Atlas

## Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2

## Deployment

- Render
- GitHub

## Development

- Git
- GitHub
- Python Virtual Environment

---

# 📂 Project Structure

```text
SpendSettle/
│
├── app.py
├── requirements.txt
├── Procfile
├── .python-version
│
├── database/
│   ├── __init__.py
│   └── database_manager.py
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── wallet.py
│   └── transaction.py
│
├── payments/
│   ├── __init__.py
│   ├── payment_method.py
│   ├── wallet_payment.py
│   └── card_payment.py
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── security_manager.py
│   ├── wallet_service.py
│   ├── finance_service.py
│   └── shared_expense_service.py
│
├── templates/
│   ├── partials/
│   │   └── navbar.html
│   │
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── wallet.html
│   ├── finance.html
│   ├── finance_history.html
│   ├── groups.html
│   ├── group_detail.html
│   ├── edit_group_expense.html
│   ├── receipt.html
│   └── profile.html
│
└── static/
    ├── style.css
    ├── brand.css
    ├── auth.css
    ├── wallet.css
    ├── finance.css
    ├── groups.css
    ├── split.css
    ├── split.js
    └── app.js
```

---

# ☁️ Cloud Architecture

SpendSettle currently runs using the following deployment architecture:

```text
Developer
    │
    │ git push
    ▼
GitHub Repository
    │
    │ Auto Deploy
    ▼
Render
    │
    │ Flask + Gunicorn
    ▼
SpendSettle Web Application
    │
    │ PyMongo
    ▼
MongoDB Atlas
```

Every deployment can be triggered automatically when changes are pushed to the production branch.

---

# 🌐 Live Deployment

The application is currently deployed and publicly accessible.

### Live Application

🔗 https://spendsettle.onrender.com

### GitHub Repository

🔗 https://github.com/MarwanElbarbary/SpendSettle

---

# ⚙️ Run Locally

## 1. Clone the repository

```bash
git clone https://github.com/MarwanElbarbary/SpendSettle.git
```

Then:

```bash
cd SpendSettle
```

---

## 2. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

SpendSettle requires environment variables for configuration.

Never store production secrets directly inside the source code.

Required variables:

```text
MONGODB_URI
SECRET_KEY
```

Example:

```text
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/
SECRET_KEY=your-secret-key
```

> ⚠️ Never commit real credentials or secret keys to GitHub.

---

# ▶️ Start the Application

Development:

```bash
python app.py
```

The application should become available at:

```text
http://127.0.0.1:5000
```

Production deployments use Gunicorn:

```bash
gunicorn app:app
```

---

# 🔒 Security Considerations

SpendSettle includes multiple application-level security concepts such as:

- Authentication
- Session-based access
- PIN verification
- Backend balance protection
- Environment variables for secrets
- Separate user financial records
- Restricted group operations
- Server-side transaction validation

Sensitive deployment information such as:

```text
MongoDB credentials
Flask SECRET_KEY
```

is stored as environment variables rather than committed to GitHub.

---

# 🔮 Future Roadmap

SpendSettle is designed to continue evolving.

Some planned ideas include:

---

## 🤖 AI Financial Coach

An intelligent assistant that can understand a user's SpendSettle financial data and answer questions such as:

```text
Where am I spending the most?

How can I reduce my spending?

Can I save 2,000 EGP this month?

Create a spending plan for the next week.

Which expense category is consuming most of my budget?
```

The assistant would analyze information such as:

- Monthly budget
- Spending categories
- Recent expenses
- Wallet activity
- Shared debts

to provide personalized budgeting insights.

---

## 📸 AI Receipt Scanner

Users will be able to upload or photograph a receipt.

The system could automatically extract:

```text
Merchant
Date
Items
Quantity
Price
Tax
Total
Currency
Expense Category
```

The user would then review the extracted information before saving it as an expense.

Proposed flow:

```text
Take Receipt Photo
        ↓
AI Vision Analysis
        ↓
Extract Receipt Data
        ↓
Review Information
        ↓
Confirm
        ↓
Create Expense
```

---

## 📈 Financial Analytics

Future versions could provide more advanced analytics such as:

- Spending trends
- Category comparisons
- Monthly reports
- Saving targets
- Spending alerts
- Financial insights

---

# 💡 What I Learned

Building SpendSettle involved much more than writing application features.

The project helped me practice thinking across the full software development lifecycle:

```text
Idea
 ↓
Requirements
 ↓
OOP Design
 ↓
Backend Architecture
 ↓
Database Design
 ↓
Frontend Development
 ↓
Feature Integration
 ↓
Debugging
 ↓
Cloud Database
 ↓
Deployment
 ↓
Production Testing
 ↓
Continuous Improvement
```

Some of the main areas explored during development include:

- Object-Oriented Programming
- Backend development
- Flask architecture
- MongoDB database design
- Authentication
- Financial transaction logic
- Service-oriented architecture
- Responsive UI design
- Git and GitHub
- Environment variables
- Cloud databases
- Production deployment
- Debugging production issues
- Product thinking

---

# 🎯 Project Philosophy

The most important idea behind SpendSettle is not a specific framework or feature.

It is the way the project evolved.

Instead of asking:

> **"What do I need to implement to finish the assignment?"**

I tried to ask:

> **"How can I turn this small idea into something that feels like a real product?"**

That mindset led to the continuous evolution of SpendSettle from a small OOP project into a deployed full-stack financial application.

---

# 👨‍💻 Developer

**Marwan Elbarbary**

Computer Science  
AI • Machine Learning • Software Development

GitHub:

https://github.com/MarwanElbarbary

---

# 🔗 Links

🌐 **Live Demo**  
https://spendsettle.onrender.com

💻 **Source Code**  
https://github.com/MarwanElbarbary/SpendSettle

---

<div align="center">

## SpendSettle

### Track. Split. Settle.

**From a simple OOP idea to a deployed full-stack financial platform.**

⭐ If you find the project interesting, feel free to star the repository.

</div>
