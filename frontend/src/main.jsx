import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import Admin from './components/Admin.jsx'
import Privacy from './components/Privacy.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
