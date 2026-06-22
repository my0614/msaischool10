function CounterPage() {
  let count = 1;
  return (
    <div className="flex justify-center mt-20">
      <div className="flex flex-col justify-center p-20 text-[50px] w-150 bg-white">
        <h1 className="text-[100px] text-center">{count}</h1>
        <div className="flex justify-between gap-10">
          <button className="bg-blue-100 w-20 rounded-full hover:bg-blue-200">
            -
          </button>
          <button className="bg-[#f3f3f3] w-50 pl-5 pr-5 rounded-[10px] hover:bg-[#eee]">
            Reset
          </button>
          <button className="bg-blue-500 w-20 rounded-full text-white hover:bg-blue-600">
            +
          </button>
        </div>
      </div>
    </div>
  );
}
