# Chef Bot - Development Documentation

## Project Overview
Chef Bot is an AI-powered recipe suggestion web application that helps users discover recipes based on their available ingredients. The application uses a FastAPI backend and React frontend to provide a modern, responsive user experience.

## Quick Start

### Backend Setup
```bash
# Clone the repository
git clone <repository-url>

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
# Create .env file in the backend directory with:
DATABASE_URL=sqlite:///./chef_bot.db  # or your PostgreSQL connection string
DEEPSEEK_API_KEY=your_deepseek_api_key

# Run the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install frontend dependencies
npm install

# Start the development server
npm start
```

## Deployment Instructions

### Docker Deployment

The easiest way to deploy Chef Bot is using Docker:

```bash
# Build and start the Docker container
docker-compose up -d --build

# The application will be available at http://localhost:8000
```

### Heroku Deployment

To deploy to Heroku:

```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create chef-bot-app

# Set environment variables
heroku config:set DEEPSEEK_API_KEY=your_deepseek_api_key
heroku config:set GOOGLE_CLIENT_ID=your_google_client_id
heroku config:set GOOGLE_CLIENT_SECRET=your_google_client_secret
heroku config:set SECRET_KEY=your_secret_key
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Push to Heroku
git push heroku main
```

### Manual Deployment

For manual deployment on a VPS or cloud server:

1. Clone the repository on your server
2. Set up environment variables in a `.env` file
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Run with a production WSGI server:
   ```bash
   cd backend
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

## Development Guidelines

### Code Structure

#### Backend (FastAPI)
- `backend/main.py`: Main FastAPI application entry point
- `backend/app/`: Application package
  - `api/`: API endpoints and routers
  - `core/`: Core application settings
  - `db/`: Database models and connection
  - `schemas/`: Pydantic schemas for data validation
  - `services/`: Business logic and external services

#### Frontend (React)
- `frontend/src/`: Source code
  - `App.tsx`: Main application component
  - `components/`: Reusable UI components
  - `services/`: API service functions
  - `types/`: TypeScript type definitions

### Coding Standards
1. **Python Style Guide**
   - Follow PEP 8 guidelines
   - Use type hints for function parameters and returns
   - Document all functions with docstrings

2. **Git Workflow**
   - Create feature branches from `develop`
   - Branch naming: `feature/feature-name`, `bugfix/bug-name`
   - Commit messages should be clear and descriptive
   - Pull requests require code review before merging

3. **Testing Requirements**
   - Unit tests for all core functionality
   - Integration tests for API endpoints
   - UI/UX testing for frontend components
   - Test coverage should be >80%

### QA Checkpoints
Each feature must pass these checks before approval:

#### Backend Checks
- [ ] API endpoints follow RESTful conventions
- [ ] Error handling is implemented
- [ ] Input validation is in place
- [ ] Database queries are optimized
- [ ] API responses are properly formatted

#### Frontend Checks
- [ ] UI is responsive on all screen sizes
- [ ] Form validation works correctly
- [ ] Error messages are user-friendly
- [ ] Loading states are handled
- [ ] Browser compatibility tested

#### Security Checks
- [ ] API keys are properly secured
- [ ] Input sanitization is implemented
- [ ] SQL injection prevention is in place
- [ ] XSS protection is implemented
- [ ] CSRF protection is enabled

### Deployment Process
1. Run all tests
2. Update version number
3. Create release branch
4. Deploy to staging
5. Perform QA testing
6. Deploy to production

## API Documentation

### Ingredient Management
```
GET /api/v1/ingredients - Get all ingredients
POST /api/v1/ingredients - Create a new ingredient
GET /api/v1/ingredients/{id} - Get a specific ingredient
PUT /api/v1/ingredients/{id} - Update an ingredient
DELETE /api/v1/ingredients/{id} - Delete an ingredient
```

### Recipe Suggestions
```
POST /api/v1/recipes/suggest?servings={servings} - Get recipe suggestions
```

### Swagger Documentation
API documentation is available at `/docs` when the backend server is running.

## Version Control
```bash
# Initialize repository
git init

# Create develop branch
git checkout -b develop

# Before pushing changes
git add .
git commit -m "descriptive message"
git push origin develop

# Create release
git checkout -b release/v1.0.0
```

## Quality Gates
Each PR must pass:
1. Automated tests
2. Code coverage requirements
3. Code review by senior developer
4. Security scan
5. Performance benchmarks

## Contact
For questions or issues:
- Create an issue in the repository
- Tag relevant developers
- Use appropriate labels

## License
[Specify License]
