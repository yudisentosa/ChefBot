# Chef Bot - Web App Specification

## 1. Overview
**Name:** Chef Bot

**Description:** Chef Bot is a web application that helps users find recipes based on available ingredients in their kitchen. Users can input, edit, or delete ingredients via a user interface. The chatbot, powered by DeepSeek, suggests dishes based on the stored ingredient data.

## 2. Technology Stack
- **Backend:** FastAPI (Python)
- **Frontend:** React (JavaScript or TypeScript)
- **Database:** PostgreSQL or SQLite (choose based on environment)
- **AI Model:** DeepSeek
- **Hosting:** To be determined based on deployment requirements

## 3. Features & Requirements

### 3.1 User Management
- Optional authentication (Login/Signup)
- Each user has a personal ingredient list

### 3.2 Ingredient Management
- UI to add, edit, and delete ingredients
- Backend API for ingredient CRUD
- Input validation to prevent duplicates and errors

### 3.3 Chatbot Functionality
- User asks: "What can I cook with these ingredients?"
- Frontend sends the query and ingredient list to the backend
- FastAPI forwards the data to DeepSeek
- DeepSeek returns dish suggestions, including:
  - Dish name
  - Required ingredients
  - Missing ingredients (if any)
  - Optional: Cooking instructions

### 3.4 AI Integration
- Use DeepSeek for NLP-based dish suggestions
- Ingredient normalization logic (handle synonyms, formats)
- Suggest similar recipes even with partial matches

### 3.5 API Design (FastAPI)
- `/ingredients` (GET, POST, PUT, DELETE)
- `/chat` (POST)
- Modular structure using routers and Pydantic models

### 3.6 Frontend (React)
- Use the UI in the bolt_ui folder as the design and layout reference
- Core components/pages:
  - Ingredient manager
  - Chatbot interaction
  - Auth (if enabled)
- Ensure responsiveness for mobile/tablet
- Display clear status for available, used, and missing ingredients

## 4. Implementation Plan

### Phase 1: Project Setup (Days 1-2)
- [ ] Initialize Git repository
- [ ] Set up Python virtual environment
- [ ] Create requirements.txt with initial dependencies
- [ ] Set up basic project structure:
  ```
  chef_bot/
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   ├── core/
  │   │   ├── db/
  │   │   ├── schemas/
  │   │   └── services/
  │   ├── main.py
  │   └── requirements.txt
  ├── frontend/
  │   ├── public/
  │   ├── src/
  │   └── package.json
  └── README.md
  ```

### Phase 2: Backend Development (Days 3-7)
- [ ] Set up FastAPI application structure
- [ ] Configure database connection (SQLite for development, PostgreSQL for production)
- [ ] Create database models and migrations
- [ ] Implement Pydantic schemas for data validation
- [ ] Develop API endpoints:
  - [ ] GET, POST, PUT, DELETE for ingredients
  - [ ] POST for chat/recipe suggestions
- [ ] Integrate DeepSeek API:
  - [ ] Set up API key configuration
  - [ ] Create service for recipe suggestions
  - [ ] Implement error handling and fallbacks

### Phase 3: Frontend Development (Days 8-14)
- [ ] Set up React application with TypeScript
- [ ] Implement component structure based on bolt_ui design
- [ ] Create reusable UI components:
  - [ ] Ingredient list with quantity adjusters
  - [ ] Unit selection dropdowns
  - [ ] Delete buttons for ingredients
  - [ ] Add ingredient form
- [ ] Implement state management (Context API or Redux)
- [ ] Create API service for backend communication
- [ ] Develop chat interface for recipe suggestions
- [ ] Add responsive design for mobile/tablet
- [ ] Implement form validation and error handling

### Phase 4: Integration and Testing (Days 15-18)
- [ ] Connect frontend to backend API
- [ ] Implement authentication (if required)
- [ ] Write unit tests for backend:
  - [ ] API endpoints
  - [ ] Service functions
  - [ ] Data validation
- [ ] Write unit tests for frontend:
  - [ ] Component rendering
  - [ ] State management
  - [ ] API integration
- [ ] Perform end-to-end testing
- [ ] Fix bugs and improve error handling

### Phase 5: Optimization and Deployment (Days 19-21)
- [ ] Optimize database queries
- [ ] Implement caching where necessary
- [ ] Set up Docker configuration:
  - [ ] Dockerfile for backend
  - [ ] Dockerfile for frontend
  - [ ] Docker Compose for local development
- [ ] Configure CI/CD pipeline
- [ ] Deploy to chosen hosting platform
- [ ] Set up monitoring and logging

### Phase 6: Documentation and Finalization (Days 22-25)
- [ ] Create API documentation with Swagger UI
- [ ] Write user guide
- [ ] Document setup instructions
- [ ] Create deployment guide
- [ ] Final testing and bug fixes
- [ ] Project handover

## 5. Development Notes
- Use .env files to store API keys and environment-specific variables
- Implement proper error handling and logging
- Use dependency injection for services in FastAPI
- Follow React best practices for component structure
- Ensure code is well-documented and follows consistent style
- Implement proper security measures for API endpoints
- Optional: Dockerize the application for easy deployment

## 6. Success Criteria
- Users can manage their ingredient inventory (add, update, delete)
- Application successfully suggests recipes based on available ingredients
- Interface is responsive and user-friendly
- System handles errors gracefully
- API responses are fast and efficient
- Code is well-documented and maintainable
- Application is secure and follows best practices
