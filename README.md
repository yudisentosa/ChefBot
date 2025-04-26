<div align="center">

# 🍳 Chef Bot

**AI-Powered Recipe Assistant**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-1.0.3-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/utensils.svg" width="100" height="100" alt="Chef Bot Logo" style="filter: invert(43%) sepia(94%) saturate(1752%) hue-rotate(194deg) brightness(99%) contrast(97%);">  

*Your AI-powered kitchen companion that suggests delicious recipes based on ingredients you already have.*

[Demo](#live-demo) • [Features](#key-features) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Deployment](#deployment)

</div>

## 📋 Overview

Chef Bot is an AI-powered web application that helps users discover recipes based on ingredients they already have in their kitchen. The application features a clean, intuitive interface where users can manage their ingredient inventory and get personalized recipe suggestions with detailed cooking instructions.

### Live Demo

🔗 [Chef Bot Live Demo](https://chef-bot.vercel.app/)

<div align="center">
<img src="https://via.placeholder.com/800x450.png?text=Chef+Bot+Screenshot" alt="Chef Bot Screenshot" width="800">
</div>

## ✨ Key Features

- **Ingredient Management**: Add, edit, and delete ingredients in your virtual pantry
- **AI-Powered Recipe Suggestions**: Get personalized recipe ideas based on your available ingredients
- **User Authentication**: Secure login with Google OAuth
- **Recipe Saving**: Save your favorite recipes for future reference
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Updates**: Instant feedback when managing ingredients or requesting recipes

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Node.js and npm (for local development)
- Supabase account
- Google OAuth credentials

### Local Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/chef-bot.git
cd chef-bot
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the project root with the following variables:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SECRET_KEY=your_secret_key_for_jwt
GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

4. **Run the application locally**

```bash
python -m uvicorn backend.api.index:app --reload
```

The application will be available at http://localhost:8000

## 🧩 Usage

### Adding Ingredients

1. Log in with your Google account
2. Click on the "Add Ingredient" button
3. Enter the ingredient name and quantity
4. Click "Save"

### Getting Recipe Suggestions

1. Ensure you have added ingredients to your pantry
2. Click on the "What can I cook?" button
3. Review the suggested recipes
4. Click on a recipe to view detailed instructions

### Saving Favorite Recipes

1. View a recipe suggestion
2. Click the "Save Recipe" button
3. Access saved recipes from your profile page

## 🏗️ Architecture

### Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Authentication**: Google OAuth
- **Deployment**: Vercel

### Project Structure

```
chef_bot/
├── backend/
│   ├── api/
│   │   └── index.py      # Main FastAPI application
│   └── db/
│       └── supabase_tables.sql  # Database schema
├── frontend/
│   └── simple.html      # Frontend interface
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
├── vercel.json         # Vercel deployment configuration
└── README.md           # Project documentation
```

### Database Schema

The application uses Supabase (PostgreSQL) with the following tables:

- **users**: Stores user information (UUID primary key)
- **ingredients**: Tracks user ingredients (UUID foreign key to users)
- **saved_recipes**: Stores user's favorite recipes (UUID foreign key to users)

## 📦 Deployment

### Deploying to Vercel

1. **Fork or clone this repository**

2. **Create a Vercel account** at [vercel.com](https://vercel.com)

3. **Install Vercel CLI**

```bash
npm install -g vercel
```

4. **Login to Vercel**

```bash
vercel login
```

5. **Deploy from your local project**

```bash
cd chef_bot
vercel
```

6. **Configure environment variables**

Add the following environment variables in the Vercel dashboard:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`

7. **Update Google OAuth settings**

Add your Vercel deployment URL to the authorized JavaScript origins in your Google Cloud Console.

## 🧪 Development

### Setting Up Supabase

1. Create a Supabase account at [supabase.com](https://supabase.com)
2. Create a new project
3. Use the SQL schema in `backend/db/supabase_tables.sql` to set up your tables
4. Copy your project URL and API keys to your environment variables

### Local Development

```bash
# Run the backend server with hot reloading
python -m uvicorn backend.api.index:app --reload

# Open the frontend directly in your browser
# or serve it with a simple HTTP server
python -m http.server --directory frontend
```

## 🔍 Testing

```bash
# Run tests
python -m pytest
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [Supabase](https://supabase.com/) - Database and authentication
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Vercel](https://vercel.com/) - Deployment platform

---

<div align="center">

**Built with ❤️ by Yudiestira Sentosa**

</div>
