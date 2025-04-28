# 🍳 Chef Bot

## AI-Powered Recipe Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-1.0.3-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

![Chef Bot Logo](https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/utensils.svg)

*Your AI-powered kitchen companion that suggests delicious recipes based on ingredients you already have.*

[Demo](#overview) • [Features](#key-features) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Deployment](#deployment)

## 📋 Overview {#overview}

Chef Bot is an AI-powered web application that helps users discover recipes based on ingredients they already have in their kitchen. The application features a clean, intuitive interface where users can manage their ingredient inventory and get personalized recipe suggestions with detailed cooking instructions.

### Live Demo

🔗 [Chef Bot Live Demo](https://mychefbot.vercel.app/)

![Chef Bot Demo - Recipe Generation in Action](documentation/Chefbot%20-%20demo.gif)
*Chef Bot in action: Generating personalized recipes based on available ingredients*

![Chef Bot Interface - Ingredient Management](documentation/chefbot%20-%20demo%20-%201.png)
*Ingredient management interface: Add, edit, and track your available ingredients*

![Chef Bot Interface - Recipe View](documentation/chefbot%20-%20demo%20-%202.png)
*Recipe view: Detailed cooking instructions with ingredients and steps*

## ✨ Key Features {#key-features}

- **Ingredient Management**: Add, edit, and delete ingredients in your virtual pantry
- **AI-Powered Recipe Suggestions**: Get personalized recipe ideas based on your available ingredients
- **User Authentication**: Secure login with Google OAuth
- **Recipe Saving**: Save your favorite recipes for future reference
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Updates**: Instant feedback when managing ingredients or requesting recipes

## 🚀 Installation {#installation}

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

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

1. **Set up environment variables**

Create a `.env` file in the project root with the following variables:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_CLIENT_ID=your_google_oauth_client_id
CHEFBOT_API_KEY=your_deepseek_api_key
```

1. **Run the application locally**

```bash
python -m uvicorn backend.api.index:app --reload
```

The application will be available at [http://localhost:8000](http://localhost:8000)

## 🧩 Usage {#usage}

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

## 🏗️ Architecture {#architecture}

### Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Authentication**: Google OAuth
- **Deployment**: Vercel

### Project Structure

```text
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

## 📦 Deployment {#deployment}

### Deploying to Vercel

1. **Fork or clone this repository**

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

1. **Install Vercel CLI**

```bash
npm install -g vercel
```

1. **Login to Vercel**

```bash
vercel login
```

1. **Deploy from your local project**

```bash
cd chef_bot
vercel
```

1. **Configure environment variables**

Add the following environment variables in the Vercel dashboard:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`

1. **Update Google OAuth settings**

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

***Built with ❤️ by Yudiestira Sentosa***
