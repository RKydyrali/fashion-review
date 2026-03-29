# AVISHU Fashion Backend

FastAPI-based backend for AVISHU fashion superapp with pre-order system.

## Features

- User authentication (JWT)
- Client, Franchise, Production, Admin roles
- Product catalog with translations (EN, RU, KK)
- Bag & Favorites management
- Order processing workflow
- Preorder batch system
- AI Try-on integration
- Personal Wardrobe (add items from catalog, create outfits)
- Virtual Try-On for outfits

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (can be migrated to PostgreSQL)
- **Authentication**: JWT
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

## Requirements

- Python 3.13+
- SQLite

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Or install from pyproject.toml
pip install -e .
```

## Running Locally

```bash
# Start the server
uvicorn app.main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Environment Variables

Create `.env` file (see `.env.example`):

```env
DATABASE_URL=sqlite:///fashion.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Project Structure

```
fashion-backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core utilities, database
│   ├── domain/       # Domain models (enums, constants)
│   ├── models/       # SQLAlchemy models
│   ├── repositories/ # Data access layer
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── main.py       # Application entry point
├── media/            # Uploaded files
├── tests/            # Test files
├── pyproject.toml    # Dependencies
└── README.md
```

## API Endpoints

### Auth
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Current user

### Catalog
- `GET /api/v1/products` - List products
- `GET /api/v1/collections` - List collections
- `GET /api/v1/feed` - Editorial feed

### Client
- `GET /api/v1/client/bag` - Get bag
- `POST /api/v1/client/bag/items` - Add to bag
- `DELETE /api/v1/client/bag/items/{id}` - Remove from bag
- `GET /api/v1/client/favorites` - Get favorites
- `POST /api/v1/client/favorites` - Add favorite
- `DELETE /api/v1/client/favorites/{id}` - Remove favorite
- `GET /api/v1/client/orders` - Get orders
- `POST /api/v1/client/orders/{id}/pickup` - Pickup order
- `GET /api/v1/client/preorders` - Get preorder batches
- `POST /api/v1/client/preorders/submit-selected` - Submit order
- `GET /api/v1/client/wardrobe/items` - Get wardrobe items
- `POST /api/v1/client/wardrobe/items` - Add to wardrobe
- `DELETE /api/v1/client/wardrobe/items/{id}` - Remove from wardrobe
- `GET /api/v1/client/wardrobe/outfits` - Get outfits
- `POST /api/v1/client/wardrobe/outfits` - Create outfit
- `DELETE /api/v1/client/wardrobe/outfits/{id}` - Delete outfit
- `GET /api/v1/client/wardrobe/summary` - Get wardrobe summary

### Franchise
- `GET /api/v1/franchise/orders` - List franchise orders
- `POST /api/v1/franchise/orders/{id}/approve` - Approve order
- `POST /api/v1/franchise/orders/{id}/reject` - Reject order
- `GET /api/v1/franchise/sales` - Sales data
- `GET /api/v1/franchise/settings` - Franchise settings

### Production
- `GET /api/v1/production/queue` - Production queue
- `POST /api/v1/production/orders/{id}/status` - Update order status
- `GET /api/v1/production/shift-status` - Shift status
- `POST /api/v1/production/start-shift` - Start shift
- `POST /api/v1/production/end-shift` - End shift

### AI Try-On
- `POST /api/v1/try-on/jobs` - Create try-on job
- `GET /api/v1/try-on/jobs/{id}` - Get job status
- `GET /api/v1/try-on/sessions` - List sessions
- `POST /api/v1/try-on/sessions` - Create session

### Admin
- `GET /api/v1/admin/products` - List products
- `POST /api/v1/admin/products` - Create product
- `PATCH /api/v1/admin/products/{id}` - Update product
- `GET /api/v1/admin/collections` - List collections
- `POST /api/v1/admin/collections` - Create collection
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/users` - Create user
- `PATCH /api/v1/admin/users/{id}` - Update user

## Deployment

### Railway
```bash
# Push to GitHub, deploy from Railway dashboard
# Set environment variables in Railway dashboard
```

### Render
```bash
# Create web service from GitHub
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Default Users (after seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@gmail.com | admin123 |
| Client | client@example.com | client123 |
| Franchise | franchise@example.com | franchise123 |
| Production | production@example.com | production123 |

## License

Proprietary - AVISHU
