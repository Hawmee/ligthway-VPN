import { createBrowserRouter } from "react-router-dom";
import MainLayout from "./pages/MainLayout";
import PeersLayout from "./pages/peers/PeersLayout";
import ServerInfoLayout from "./pages/server-info/ServerInfoLayout";


const router = createBrowserRouter([
    {
        path:'/',
        element : <MainLayout />,
        children: [
            {
                path: '',
                element: <PeersLayout />
            },
            {
                path: 'logs',
                element: <ServerInfoLayout/>
            } 
        ]
    }
])

export default router