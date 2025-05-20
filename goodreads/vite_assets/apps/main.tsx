import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

createRoot(document.getElementById('reactRoot')!).render(
  <StrictMode>
      <div>Hello World</div>
  </StrictMode>,
)