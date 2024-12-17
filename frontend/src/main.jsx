
    import { StrictMode } from 'react'
    import { createRoot } from 'react-dom/client'
    import './index.css'
    import './style.css'
    import HumanPlayerInterface from './components/HumanPlayer/HumanPlayerInterface'

    const root = createRoot(document.getElementById('root'))
    root.render(
        <StrictMode>
            <HumanPlayerInterface playerPort={6060} />
        </StrictMode>
    )
    