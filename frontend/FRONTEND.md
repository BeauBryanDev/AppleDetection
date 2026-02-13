# 🍎 Apple Yield Estimator — Frontend

A modern, responsive **React** dashboard for orchard management and AI‑powered apple yield estimation.  
This frontend connects to a FastAPI backend (YOLOv8s + ONNX) to provide farmers with real‑time apple detection, historical tracking, and analytics.

![App Screenshot](../eg_test.png)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
  - [Development Server](#development-server)
  - [Build for Production](#build-for-production)
- [Architecture Deep Dive](#architecture-deep-dive)
  - [1. API Layer – Bridge to Backend](#1-api-layer--bridge-to-backend)
  - [2. Pages – What Users See](#2-pages--what-users-see)
  - [3. Components – Reusable Building Blocks](#3-components--reusable-building-blocks)
  - [4. Context – Global State Management](#4-context--global-state-management)
  - [5. Layouts – Page Wrappers](#5-layouts--page-wrappers)
- [Data Flow – Request Lifecycle](#data-flow--request-lifecycle)
- [Environment Variables](#environment-variables)
- [Scripts](#scripts)
- [Styling Strategy](#styling-strategy)
- [Connecting to the Backend](#connecting-to-the-backend)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## 🚀 Overview

The **Apple Yield Estimator Frontend** is a single‑page application (SPA) built with **React** and **Vite**. It provides an intuitive interface for:

- Uploading orchard images and receiving instant apple counts (red, green, damaged).
- Managing farms, orchards, and trees.
- Viewing historical yield data and analytics dashboards.
- User authentication and profile management.

The frontend is designed to mirror the backend structure – each API endpoint group has a corresponding JavaScript module in the `src/api/` folder, making the codebase predictable and easy to extend.

---

## 🛠️ Tech Stack

| Category          | Technology                         | Purpose                               |
|-------------------|------------------------------------|---------------------------------------|
| **Core**          | React 18                           | UI library                           |
| **Build Tool**    | Vite                               | Fast dev server, optimized builds    |
| **Routing**       | React Router v6                   | Page navigation, protected routes    |
| **HTTP Client**   | Axios                              | Backend communication, interceptors  |
| **Styling**       | Tailwind CSS                      | Utility‑first, responsive design     |
| **State Mgmt**    | Context API                       | Global auth state                    |
| **Code Quality**  | ESLint                            | Linting, error prevention            |
| **Package Mgr**   | npm / yarn                        | Dependency management                |

---

## 📁 Project Structure

```
frontend/
├── index.html # Entry HTML (React mounts here)
├── vite.config.js # Vite configuration
├── tailwind.config.js # Tailwind CSS configuration
├── postcss.config.js # PostCSS plugins (Tailwind, autoprefixer)
├── eslint.config.js # ESLint rules
├── package.json # Dependencies and scripts
│
├── src/
│ ├── main.jsx # App entry – renders <App /> with providers
│ ├── App.jsx # Main component – defines routes & layouts
│ ├── App.css # Global styles
│ ├── index.css # Tailwind imports
│ │
│ ├── api/ # ** Backend mirror ** – one file per route group
│ │ ├── axios.js # Axios instance with interceptors (JWT, errors)
│ │ ├── auth.js # Login, register, logout, refresh
│ │ ├── users.js # Get/update user profile
│ │ ├── estimator.js # ⭐ Upload image, get apple detection results
│ │ ├── farming.js # Orchard & tree CRUD
│ │ ├── analytics.js # Yield statistics, charts data
│ │ └── history.js # Past estimation logs
│ │
│ ├── pages/ # Full-page components (routed)
│ │ ├── Login.jsx
│ │ ├── Register.jsx
│ │ ├── Dashboard.jsx # Overview cards, recent activity
│ │ ├── Estimator.jsx # ⭐ Image upload, preview, results
│ │ ├── Farming.jsx # Manage orchards/trees
│ │ ├── Analytics.jsx # Charts, trends, class distribution
│ │ ├── History.jsx # Table of past estimations
│ │ ├── Profile.jsx # User settings
│ │ └── Users.jsx # Admin – user management
│ │
│ ├── layouts/ # Page wrappers
│ │ ├── AuthLayout.jsx # Centered form layout (login/register)
│ │ └── DashboardLayout.jsx # Header + Sidebar + main content
│ │
│ ├── components/ # Reusable UI pieces
│ │ ├── ui/ # Atomic components
│ │ │ ├── Button.jsx
│ │ │ ├── Card.jsx
│ │ │ ├── Input.jsx
│ │ │ └── Label.jsx
│ │ └── common/ # App‑specific components
│ │ ├── Header.jsx # Top navbar with user menu
│ │ └── Sidebar.jsx # Navigation links
│ │
│ ├── context/ # Global state
│ │ └── AuthContext.jsx # Provides user, token, login, logout
│ │
│ ├── assets/ # Static images/icons
│ └── public/ # Public assets (vite.svg)
│
├── .env.example # Environment variables template
```

---

## 🔑 Key Features

- **React Router** – Routing and navigation
- **Axios** – HTTP client for backend requests
- **Tailwind CSS** – Utility‑first, responsive design
- **Context API** – Global state management
- **ESLint** – Linting, error prevention
- **Vite** – Fast dev server, optimized builds

---

## 💻 Installation & Setup

### Prerequisites

- **Node.js** 18+ (LTS recommended)
- **npm** 9+ or **yarn** 1.22+
- Backend API running (see [Backend README](../app/BACKEND.md))

### Step‑by‑Step

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/apple-yield-estimator.git
   cd apple-yield-estimator/frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**

   ```bash
   npm run dev
   # or
   yarn dev
   ```
Edit .env and set your backend URL:
```
VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```
4. **Open the app in your browser**

   ```bash
   open http://localhost:3000
   ```

---

## 🚀 Usage

### Development Server

The development server is a fast, hot‑reloading environment that automatically rebuilds the app when you make changes. It's perfect for rapid development and testing.

To start the development server, run the following command:

```bash
npm run dev
# or
yarn dev
```

This will start the server on `http://localhost:3000` by default. You can now access the app and start making changes.

### Build for Production

To build the app for production, run the following command:

```bash
npm run build
# or
yarn build
```

This will generate a static build of the app in the `dist/` directory. You can then deploy the contents of this directory to a web server.

---

## 📐 Architecture Deep Dive

The frontend is built with **React** and **Vite**. It uses **React Router** for routing and navigation, and **Axios** for making API requests. The app is structured into the following components:

- `App.jsx` – The main component that renders the app based on the user's authentication status.
- `App.css` – Global styles for the app.
- `index.css` – Tailwind imports.
- `api/` – Backend mirror – one file per route group.
- `pages/` – Full-page components (routed).
- `layouts/` – Page wrappers.
- `components/` – Reusable UI pieces.
- `context/` – Global state.
- `assets/` – Static images/icons.

### 1. API Layer – Bridge to Backend

The `api/` folder contains one file per route group. Each file exports a function that returns an Axios instance with interceptors (JWT, error handling). The interceptors are used to add authentication headers to requests and handle errors.

## 1. API Layer – Bridge to Backend
Folder: src/api/

This layer mirrors your backend routers. Each file exports functions that call a specific group of endpoints.

File	Backend Router	Example Call
auth.js	/auth	login(email, password)
estimator.js	/estimator	uploadImage(file) → apple counts
farming.js	/farming	getOrchards()
history.js	/history	getUserHistory(userId)
axios.js is the heart – it creates a preconfigured Axios instance:

Base URL from VITE_API_URL

Automatically attaches JWT token to Authorization header

Global error handling (401 → logout, 500 → show toast)

Parses responses consistently.

## 2. Pages – What Users See
Folder: src/pages/

Each .jsx file is a full page mapped to a route in App.jsx.

Star of the show: Estimator.jsx

Drag‑and‑drop image uploader (or click to browse).

Preview selected image.

Calls estimator.uploadImage() with FormData.

Displays results: total apples, red/green/damaged counts.

Shows annotated image with bounding boxes (base64 from backend).

"Save to History" button stores the estimation.

## 3. Components – Reusable Building Blocks
Folders: components/ui/ and components/common/

## Data Flow – Request Lifecycle
```
1. USER ACTION
   └─ Farmer clicks "Upload" in Estimator.jsx

2. EVENT HANDLER
   └─ handleSubmit() → FormData.append('image', file)

3. API CALL (src/api/estimator.js)
   └─ export const uploadImage = (file) => axios.post('/estimator/predict', formData)
         └─ axios.interceptors.request → adds "Bearer <token>"

4. BACKEND PROCESSING
   └─ FastAPI → ONNX Runtime → YOLOv8s → Apple counts + annotated image

5. RESPONSE
   └─ { total_apples: 47, red: 32, green: 10, damaged: 5, annotated_image: "base64..." }

6. UI UPDATE
   └─ Estimator.jsx → setResult(data) → re-renders with:
         ├─ Annotated image
         ├─ Count cards (red, green, damaged)
         └─ "Save to History" button

7. PERSISTENCE (optional)
   └─ history.js → POST /history with result

```
## Environment Variables
```
VITE_API_URL=http://localhost:8000/api/v1
# Optional: VITE_APP_NAME=Apple Yield Estimator
```

## Scripts

```
Command	Action
npm run dev	Start Vite dev server (HMR)
npm run build	Build for production to dist/
npm run preview	Preview production build locally
npm run lint	Run ESLint on all source files
npm run format	Run Prettier on all source files
```

## Styling Strategy – Tailwind CSS
This project uses Tailwind CSS for styling – a utility‑first framework that speeds up development.

Configuration:

tailwind.config.js – Custom theme, colors, dark mode (class strategy).

postcss.config.js – Processes Tailwind + autoprefixer.

index.css – Imports Tailwind layers.

Example component:
```
jsx
<Card className="p-6 shadow-lg hover:shadow-xl transition-shadow">
  <Button variant="primary" className="w-full md:w-auto">
    Upload Image
  </Button>
</Card>
```

### Benefits:

No CSS files per component.

Consistent spacing/colors.

Responsive design (e.g., md:w-auto).

Dark mode ready.

## Connecting to the Backend
This frontend expects your Apple Yield Estimator API to be running.

Variable	Default Value	Description
VITE_API_URL	http://localhost:8000/api/v1	Base URL for all API requests
CORS: Ensure your backend allows requests from http://localhost:5173 (or your deployed frontend URL).

## 🙏 Acknowledgments
Roboflow – Dataset annotation & export.

Ultralytics – YOLOv8 object detection framework.

Vite – Incredible build tool.

Tailwind CSS – Makes styling fun again.

