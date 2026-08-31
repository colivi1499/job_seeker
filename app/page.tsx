"use client";
import { useState } from "react";

function TextInputExample() {
  // 1. Initialize state to hold the input value
  const [text, setText] = useState('');

  // 2. Update state whenever the user types
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
  };

  return (
    <div>
      <label 
      htmlFor="user_description">Enter information about the job you're looking for:
      </label>
      <input
        id="user_description"
        type="text"
        value={text}
        onChange={handleChange}
        placeholder="Type something about the job you want, or paste your resume..."
        className="mt-2 w-full"
      />
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Welcome to job_seeker. Let's find you some jobs.
          </h1>
          <TextInputExample />
        </div>
      </main>
    </div>
  );
}
