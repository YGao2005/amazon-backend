# Smart Recipe App Backend

A FastAPI-based backend for a Smart Recipe App that helps users manage ingredients, generate recipes using AI, and track food expiration. Built for hackathon speed and simplicity.

## Features

- **Ingredient Management**: Add, update, and track ingredients with expiration dates
- **AI-Powered Recipe Generation**: Generate recipes based on available ingredients using Gemini Flash
- **Ingredient Recognition**: Scan images to identify ingredients using Groq with Llama Vision
- **Recipe Image Generation**: Create appealing recipe images using Gemini 2.0
- **Expiration Tracking**: Monitor ingredient freshness and get alerts for expiring items
- **User Preferences**: Manage dietary restrictions and cooking preferences
- **Waste Management**: Track and analyze food waste patterns

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: Firebase Firestore
- **File Storage**: Firebase Storage
- **AI Services**:
  - Groq with Llama 4 Vision (ingredient recognition)
  - Gemini Flash (recipe generation)
  - Gemini 2.0 (image generation)

## Project Structure

```
smart_recipe_app/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── ingredients.py      # Ingredient management endpoints
│   │   ├── recipes.py          # Recipe management endpoints
│   │   ├── users.py            # User preferences endpoints
│   │   └── expiration.py       # Expiration management endpoints
│   ├── core/
│   │   └── config.py           # Configuration and settings
│   ├── models/                 # Pydantic data models
│   │   ├── ingredient.py       # Ingredient models
│   │   ├── recipe.py           # Recipe models
│   │   ├── user.py             # User preference models
│   │   └── expiration.py       # Expiration management models
│   ├── services/
│   │   ├── ai/                 # AI service integrations
│   │   │   ├── vision.py       # Groq vision service
│   │   │   ├── recipe_generator.py  # Gemini recipe generation
│   │   │   └── image_generator.py   # Gemini image generation
│   │   └── firebase/
│   │       └── firestore.py    # Firebase service layer
│   └── utils/                  # Utility functions
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Firebase project with Firestore and Storage enabled
- API keys for Groq and Google Gemini

### 1. Clone and Setup Environment

```bash
# Navigate to the project directory
cd smart_recipe_app

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Firestore Database and Firebase Storage
3. Create a service account:
   - Go to Project Settings > Service Accounts
   - Generate a new private key
   - Download the JSON file

### 3. Environment Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Fill in your configuration in `.env`:

```env
# Firebase Configuration (from your service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_CERT_URL=your-client-cert-url

# AI Service API Keys
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key

# Application Settings
APP_NAME=SmartRecipeApp
DEBUG=True
API_PREFIX=/api/v1
```

### 4. Get API Keys

#### Groq API Key
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up/login and create an API key
3. Add it to your `.env` file

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add it to your `.env` file

### 5. Run the Application

```bash
# Start the development server
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## API Endpoints

### Ingredients
- `GET /api/v1/ingredients/` - List all ingredients
- `POST /api/v1/ingredients/` - Create new ingredient
- `GET /api/v1/ingredients/{id}` - Get specific ingredient
- `PUT /api/v1/ingredients/{id}` - Update ingredient
- `DELETE /api/v1/ingredients/{id}` - Delete ingredient
- `POST /api/v1/ingredients/scan` - Scan image for ingredients
- `POST /api/v1/ingredients/upload-image/{id}` - Upload ingredient image
- `GET /api/v1/ingredients/expiring/soon` - Get expiring ingredients

### Recipes
- `GET /api/v1/recipes/` - List all recipes
- `POST /api/v1/recipes/` - Create new recipe
- `GET /api/v1/recipes/{id}` - Get specific recipe
- `PUT /api/v1/recipes/{id}` - Update recipe
- `DELETE /api/v1/recipes/{id}` - Delete recipe
- `POST /api/v1/recipes/generate` - Generate recipe from ingredients
- `POST /api/v1/recipes/{id}/cook` - Mark recipe as cooked
- `POST /api/v1/recipes/upload-image/{id}` - Upload recipe image
- `GET /api/v1/recipes/search/by-ingredients` - Search recipes by ingredients
- `GET /api/v1/recipes/popular` - Get popular recipes

### User Preferences
- `GET /api/v1/users/preferences` - Get user preferences
- `POST /api/v1/users/preferences` - Create user preferences
- `PUT /api/v1/users/preferences` - Update user preferences
- `GET /api/v1/users/stats` - Get user cooking statistics
- `GET /api/v1/users/profile` - Get complete user profile
- `POST /api/v1/users/preferences/reset` - Reset preferences to default
- `GET /api/v1/users/cooking-history` - Get cooking history

### Expiration Management
- `GET /api/v1/expiration/summary` - Get expiration summary
- `GET /api/v1/expiration/alerts` - Get expiration alerts
- `GET /api/v1/expiration/settings` - Get expiration settings
- `PUT /api/v1/expiration/settings` - Update expiration settings
- `POST /api/v1/expiration/waste-log` - Log wasted ingredient
- `GET /api/v1/expiration/waste-stats` - Get waste statistics
- `GET /api/v1/expiration/recipe-recommendations` - Get recipe recommendations for expiring ingredients
- `GET /api/v1/expiration/waste-logs` - Get all waste logs
- `DELETE /api/v1/expiration/waste-log/{id}` - Delete waste log

## Development Notes

### Mock Data
The AI services include mock implementations that work without API keys for development and testing. Set `DEBUG=True` in your environment to see detailed logging.

### Single User System
This is designed as a single-user system for hackathon simplicity. All user data is stored under a default user ID.

### Error Handling
The API includes comprehensive error handling with meaningful HTTP status codes and error messages.

### CORS
CORS is enabled for all origins in development. Restrict this in production.

## Deployment

### Environment Variables for Production
```env
DEBUG=False
# Add your production Firebase and API configurations
```

### Docker (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Firebase Connection Issues**
   - Verify your service account JSON is correct
   - Check that Firestore and Storage are enabled
   - Ensure your private key is properly formatted with `\n` characters

2. **AI Service Errors**
   - Verify your API keys are correct
   - Check API quotas and limits
   - The app will fall back to mock data if AI services fail

3. **Import Errors**
   - Make sure you're in the virtual environment
   - Install all requirements: `pip install -r requirements.txt`

### Logs
Check the console output for detailed error messages and debugging information.

## Contributing

This is a hackathon project focused on rapid development. For production use, consider:
- Adding authentication and authorization
- Implementing proper multi-user support
- Adding comprehensive testing
- Improving error handling and validation
- Adding rate limiting and security measures

## License

This project is created for hackathon purposes. Please check with your hackathon organizers for licensing requirements.