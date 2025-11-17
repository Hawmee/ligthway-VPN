import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { RouterProvider } from 'react-router-dom'
import router from './router.tsx'
import { HeroUIProvider } from '@heroui/react'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HeroUIProvider>
      <App>
        <RouterProvider router={router} />
      </App>
    </HeroUIProvider>
  </StrictMode>,
)
