import { type ReactNode } from 'react'
import './styles/App.css'

interface propsType {
  children?:ReactNode;
}

function App({children} : propsType ) {

  return (
    <>
      <div className='h-full w-full'>
        {children}
      </div>
    </>
  )
}

export default App
