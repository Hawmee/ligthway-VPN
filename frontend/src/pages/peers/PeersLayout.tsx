import { useEffect, useState, type JSX } from 'react'
import Table from '../../components/tables/Table'
import { get_peers } from '../../services/Peers';

function PeersLayout() : JSX.Element {

  const [data , setData] = useState<any[]>([]);
    useEffect(()=>
    {
        const fetch_peers = async () => {
            const peers = await get_peers();
            setData(peers);
        } 

        fetch_peers();
    } , [])
  
  return (
    <>
    <div className='h-full w-full'>
      <div className=' h-full w-full flex flex-col items-center'>
        <div className='text-xl text-gray-500 my-8 mr-12' >
          Peers
        </div>
        <div className=' h-full w-full'>
          <Table data={data} setData={setData}/>
        </div>
      </div>
    </div>
    </>
  )
}

export default PeersLayout