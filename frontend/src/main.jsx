import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './style.css'
import MonopolyBoard from './components/Board/MonopolyBoard.jsx'
// import MonopolyBoard from './MonopolyBoard.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* <MonopolyBoard /> */}
    <MonopolyBoard />
  </StrictMode>,
)
