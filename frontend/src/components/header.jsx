import React from 'react'
import { useNavigate } from 'react-router-dom';


function Header() {
  const nav = useNavigate();

  return (
    <div className='w-full flex justify-end gap-6 p-4'>
        <h3 onClick={()=>nav('/')} className='font-bold hover:underline'>Home</h3>
        <h3 onClick={()=>nav('/getPracticeQues')} className='font-bold hover:underline'>Vid to Ques</h3>
        <a href="https://clarityhub.duckdns.org/ai-tutor"><h3 className='font-bold hover:underline'>Video Gen</h3></a>
        <h3 onClick={()=>nav('/profile')} className='font-bold hover:underline'>Profile</h3>
    </div>
  )
}

export default Header