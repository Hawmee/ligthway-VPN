import { useState, type ReactNode } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './styles/App.css'

interface propsType {
  children?:ReactNode;
}

function App({children} : propsType ) {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        {children}
      </div>
    </>
  )
}

export default App
