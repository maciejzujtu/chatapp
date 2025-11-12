export default function LandingPage() {
  return (
    <div className="w-full h-screen flex flex-col justify-center items-center text-center bg-gray-800 ">
        <div className="bg-stone-900 w-200 h-auto rounded-xl shadow-xl outline-4 outline-stone-200">

                 <h1 className="text-4xl font-bold text-white m-4"> wellcome  'user'</h1>
                    <p  className="text-gray-300">here you can chat with some random person</p>
          
            <div className="w-full h-70 flex flex-row gap-26 justify-center items-center">
                
                <button className="bg-stone-400 w-60 h-20 rounded-2xl text-xl font-bold hover:bg-stone-100" > chose thread </button>
                <button className="bg-stone-400 w-60 h-20 rounded-2xl text-xl font-bold hover:bg-stone-100" > create your own </button>
                
            </div>


        </div>

    </div>
  );

}