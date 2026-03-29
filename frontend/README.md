# AVISHU Mobile App

Expo (React Native) mobile application for AVISHU fashion superapp.

## Features

- **Client Role**: Browse catalog, add to bag, favorites, place orders
- **Personal Wardrobe**: Add items from catalog, create outfits, virtual try-on
- **Franchise Role**: View and manage orders, sales dashboard
- **Production Role**: View production queue, update order status
- **Virtual Try-On**: AI-powered try-on experience
- **Multi-language**: English, Russian, Kazakh support

## Tech Stack

- **Framework**: Expo SDK 54 (React Native)
- **Navigation**: Expo Router
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Styling**: NativeWind (Tailwind)

## Requirements

- Node.js 18+
- npm or yarn
- Expo CLI

## Installation

```bash
# Install dependencies
npm install

# Or using yarn
yarn install
```

## Running Locally

```bash
# Start development server
npm start

# Or with specific platform
npm run android
npm run ios
npm run web
```

## Project Structure

```
fashion-expo/
├── app/                    # Expo Router pages
│   ├── (tabs)/            # Tab navigation screens
│   ├── (admin)/           # Admin screens
│   ├── franchise/         # Franchise screens
│   ├── production/        # Production screens
│   └── wardrobe.tsx       # Wardrobe screen
├── src/
│   ├── components/         # Reusable components
│   ├── i18n/             # Internationalization
│   ├── services/         # API services
│   └── state/            # State management
├── app.json              # Expo configuration
├── package.json          # Dependencies
└── README.md
```

## Screens

### Client Screens (Tab Navigation)
- **Home** - Featured collections and products
- **Collections** - Browse product catalog
- **Bag** - Shopping bag and checkout
- **Orders** - Order history and tracking
- **Profile** - User profile and settings

### Other Screens
- **Wardrobe** - Personal wardrobe and outfits
- **Login/Signup** - Authentication
- **Product Detail** - Product information
- **Try-On** - Virtual try-on experience
- **Franchise Dashboard** - For franchise users
- **Production Dashboard** - For production users
- **Admin Panel** - For admin users

## API Configuration

Update the API base URL in `src/services/api/index.ts` for production:

```typescript
const API_BASE_URL = "https://your-backend-url.com";
```

## Build for Production

### Android
```bash
npx expo prebuild
npx expo run:android --variant release
```

### iOS
```bash
npx expo prebuild
npx expo run:ios
```

### Web
```bash
npx expo export
```

## Deployment

### Expo EAS
```bash
# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Build
eas build -p android
eas build -p ios
```

### Web (Static Export)
```bash
# Deploy to Vercel, Netlify, etc.
npx expo export --platform web
```

## Environment Variables

Create `.env` file for production:

```env
EXPO_PUBLIC_API_URL=https://your-backend-url.com
```

## Default Test Users

| Role | Email | Password |
|------|-------|----------|
| Client | client@example.com | client123 |
| Franchise | franchise@example.com | franchise123 |
| Production | production@example.com | production123 |
| Admin | admin@gmail.com | admin123 |

## License

Proprietary - AVISHU
