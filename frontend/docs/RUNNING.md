# Setup and Run MoniAgent Frontend

This guide describes how to set up and run the MoniAgent Frontend application.

## Prerequisites

- Node.js 18 or later
- npm (usually installed with Node.js)
- A running instance of the MoniAgent Backend (default: http://localhost:8000)

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Configuration

The frontend connects to the backend API. By default, it looks for the API at `http://localhost:8000/v1`.

To configure a different API URL, create a `.env.local` file in the `frontend` directory:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://your-backend-url:8000/v1
```

## Running the Development Server

To start the frontend in development mode:

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## Building for Production

To build the application for production:

```bash
npm run build
```

To start the production server after building:

```bash
npm run start
```

## Project Structure

- `src/app`: Next.js App Router pages and layouts
- `src/components`: Reusable UI components
- `src/lib`: Utilities and API clients
  - `api`: API client modules (auth, chat, expenses, etc.)
  - `auth.ts`: Client-side token storage management

## Common Issues

### "eslint" or "next" not recognized
If you see errors like `'next' is not recognized`, ensure you have installed dependencies (`npm install`) and are running the commands from within the `frontend` directory.

### API Connection Error
If the frontend cannot connect to the backend:
1. Ensure the backend is running.
2. Check your browser console for CORS errors.
3. Verify the `NEXT_PUBLIC_API_URL` is correct in `.env.local`.
