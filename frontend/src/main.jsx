import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import './index.css'

// Lazy-load secondary pages to reduce initial bundle size
const Admin = lazy(() => import('./components/Admin.jsx'))
const About = lazy(() => import('./components/About.jsx'))
const Compare = lazy(() => import('./components/Compare.jsx'))
const Gallery = lazy(() => import('./components/Gallery.jsx'))
const Privacy = lazy(() => import('./components/Privacy.jsx'))
const Status = lazy(() => import('./components/Status.jsx'))
const Account = lazy(() => import('./components/Account.jsx'))
const NotFound = lazy(() => import('./components/NotFound.jsx'))

function PageLoader() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-600 text-sm">Loading...</p>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/about" element={<About />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/status" element={<Status />} />
        <Route path="/account" element={<Account />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)
