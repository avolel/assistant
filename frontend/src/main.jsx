// React application entry point.
// createRoot() is the React 18 API for mounting the app onto a DOM node.
// document.getElementById('root') targets the <div id="root"> in index.html.
// StrictMode renders components twice in development to surface side-effect bugs —
// it has no effect in production builds.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)