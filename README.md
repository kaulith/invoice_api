# 📘 Invoice Application (Flask)

A simple invoice management application built using Flask, Peewee ORM, and HTML templates. The app includes basic authentication, customer management, item management, invoice generation, GST calculation, settings, and PDF generation.

## 🚀 Features

* User Login & Signup
* Dashboard Overview
* Customers CRUD
* Items CRUD
* Invoice creation with item list
* GST calculations
* ARN number integration
* Invoice PDF generation
* Lightweight UI using HTML templates
* Settings page (theme + GST settings)
* Secure session-based authentication

## 🗂️ Project Structure (Basic Overview)

```
invoice_api/
│
├── app.py
├── config.py
├── models.py
├── utils.py
├── requirements.txt
│
├── blueprints/
│   ├── auth/
│   ├── customer/
│   ├── invoice/
│   ├── item/
│   └── setting/
│
├── templates/
└── bruno/
```

## 🛠️ Tech Stack

* Python
* Flask
* Peewee ORM
* SQLite
* HTML + Jinja Templates
* WeasyPrint (PDF generation)

## 🔧 Setup Instructions

1. Clone the repo
2. Create virtual environment
3. Install dependencies
4. Run the app

Commands:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 📸 Screenshots

Example:


### Login/Signup
<img width="565" height="441" alt="Screenshot 2025-11-15 at 1 47 52 PM" src="https://github.com/user-attachments/assets/ab700250-0a69-4f03-9ba2-2d079818c16c" /><img width="557" height="565" alt="Screenshot 2025-11-15 at 1 47 57 PM" src="https://github.com/user-attachments/assets/cd2ea29a-219f-40c1-8553-019f2bea88d5" />

### Dashboard
<img width="1512" height="982" alt="Screenshot 2025-11-15 at 1 48 10 PM" src="https://github.com/user-attachments/assets/1698bfa3-899b-4f99-8501-aa19bc6d98b5" />

### Customer page
<img width="1512" height="982" alt="Screenshot 2025-11-15 at 1 48 46 PM" src="https://github.com/user-attachments/assets/67532077-9718-4fd4-9163-e0739c1aa52c" />

### Items page
<img width="1512" height="982" alt="Screenshot 2025-11-15 at 1 48 53 PM" src="https://github.com/user-attachments/assets/23b160ca-cc53-444c-a2f1-6b41db74e3cc" />

### Invoice page
<img width="1512" height="982" alt="Screenshot 2025-11-15 at 1 48 59 PM" src="https://github.com/user-attachments/assets/d5170c7f-caf8-411d-80b8-bb7ed151824e" />

### ADD and Edit detail pages
<img width="734" height="314" alt="Screenshot 2025-11-15 at 1 52 17 PM" src="https://github.com/user-attachments/assets/2f666cad-3f1c-4576-aa84-78eeb16ce085" />
<img width="783" height="321" alt="Screenshot 2025-11-15 at 1 52 32 PM" src="https://github.com/user-attachments/assets/a79769d1-82d9-4619-9ee1-f0d8539aa4d4" />
<img width="732" height="425" alt="Screenshot 2025-11-15 at 1 52 38 PM" src="https://github.com/user-attachments/assets/61613024-e4be-42af-b388-969d55c62317" />
<img width="536" height="434" alt="Screenshot 2025-11-15 at 1 52 45 PM" src="https://github.com/user-attachments/assets/0c39c616-9358-43bb-8ea5-e9e027810012" />
<img width="578" height="346" alt="Screenshot 2025-11-15 at 1 52 53 PM" src="https://github.com/user-attachments/assets/6e3f78e5-b0ba-42e6-9672-f62da3cd048f" />
<img width="899" height="753" alt="Screenshot 2025-11-15 at 1 53 00 PM" src="https://github.com/user-attachments/assets/91e06687-7a31-4453-9134-a327a13dbea9" />


### Invoice view

<img width="929" height="768" alt="Screenshot 2025-11-15 at 1 53 23 PM" src="https://github.com/user-attachments/assets/205315ed-b8aa-43a6-983d-a3af48abc545" />

### Settings

<img width="879" height="778" alt="Screenshot 2025-11-15 at 1 53 33 PM" src="https://github.com/user-attachments/assets/4463611d-15e2-4b17-83d1-ab52f6b86893" />


## 📬 API Testing (Bruno Collection)

The project includes a Bruno collection for testing all API endpoints, available in:

```
/bruno
```

## 📌 Branches Summary

* backend-only → Contains only fully functional backend
* after-frontend → Contains backend + frontend templates
* final → Clean merged version for submission

## 🎯 Key Highlights

* Modular Architecture: Clean separation of concerns using Flask blueprints
* Database ORM: Peewee ORM for simple and efficient database operations
* PDF Generation: Professional invoice PDFs using WeasyPrint
* Session Management: Secure user authentication with Flask sessions
* API Ready: RESTful endpoints tested with Bruno collection
* Lightweight: Minimal dependencies, easy to deploy

## 📝 Database Schema
### The application uses the following main models:

* User: Authentication and user management
* Customer: Customer information storage
* Item: Product/service catalog
* Invoice: Invoice headers with customer and GST details
* InvoiceItem: Line items for each invoice

## 🔐 Security Features

* Password hashing for user credentials
* Session-based authentication
* Protected routes requiring login

## 🚧 Future Enhancements

* Multi-currency support
* Email invoice delivery
* Invoice templates customization
* Export to Excel/CSV

## Note: Make sure to update the values in config.py and customize settings as per your requirements before deployment.
