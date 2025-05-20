import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// import './index.css'

createRoot(document.getElementById('reactRoot')!).render(
  <StrictMode>
      <div>Hello World</div>
  </StrictMode>,
)